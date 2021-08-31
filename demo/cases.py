import spacy
import spacy.symbols
from loguru import logger
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.templating import Jinja2Templates

from .constants import AFOR_COORDINATES, MAP_PROVIDER_ATTRIBUTION, MAP_PROVIDER_URL
from .geo import Coordinates, find_nearest_place
from .models import MapOptions
from .repos import FrequencyRepo

# TODO: create presenters
templates = Jinja2Templates(directory="templates")


class HomePage:
    @staticmethod
    async def execute(request):
        context = {"request": request}
        return templates.TemplateResponse("index.html", context)


class LeafletMapPage:
    def __init__(self, frequency_repo: FrequencyRepo):
        self._frequency_repo = frequency_repo
        self._map_config = MapOptions(
            center=list(AFOR_COORDINATES),
            provider_url=MAP_PROVIDER_URL,
            provider_attribution=MAP_PROVIDER_ATTRIBUTION,
        )

    def _prepare_frequencies(self, place):
        _table = self._frequency_repo.fetch_frequency_table(place)
        _max_freq = max(_table.values())
        return [[w, f / _max_freq] for w, f in _table.items()]

    async def execute(self, request):
        frequencies = [
            (list(place), self._prepare_frequencies(place))
            for place in self._frequency_repo.places
        ]
        context = {
            "map_config": self._map_config,
            "frequencies": frequencies,
            "request": request,
        }
        return templates.TemplateResponse("map.html", context)


class SharePage:
    def __init__(self, frequency_repo: FrequencyRepo):
        self._frequency_repo = frequency_repo
        self._nlp = spacy.load("it_core_news_sm")

    async def execute(self, target: Coordinates, text: str, request):
        if request.method == "POST":
            logger.debug(f"Receiving text from {target}: {text}")
            nearest_place, _ = find_nearest_place(target, self._frequency_repo.places)

            doc = self._nlp(text)
            for token in doc:
                if token.pos in (
                    spacy.symbols.ADV,
                    spacy.symbols.NOUN,
                    spacy.symbols.VERB,
                    spacy.symbols.ADJ,
                ):
                    self._frequency_repo.update_frequency(nearest_place, token.lemma_)

        context = {"request": request}
        return templates.TemplateResponse("share.html", context)


class SpeechToText:
    def __init__(self):
        pass

    async def execute(self, request, audio):
        logger.debug(audio)
        return JSONResponse("")


class Ping:
    def __init__(self):
        self._response = "Pong!"

    async def execute(self, request):
        logger.debug(self._response)
        return PlainTextResponse(self._response)
