from datetime import datetime
from os.path import dirname, join

import pytest
import scrapy
from city_scrapers_core.constants import BOARD, PASSED, TENTATIVE
from city_scrapers_core.utils import file_response
from freezegun import freeze_time
from scrapy.settings import Settings

from city_scrapers.spiders.det_downtown_development_authority import (
    DetDowntownDevelopmentAuthoritySpider,
)

# Shared properties between two different page / meeting types

LOCATION = {
    "name": "DEGC, Guardian Building",
    "address": "500 Griswold St, Suite 2200, Detroit, MI 48226",
}

TITLE = "Board of Directors"

test_response = file_response(
    join(dirname(__file__), "files", "det_downtown_development_authority.html"),
    url="http://www.degc.org/public-authorities/dda/",
)
freezer = freeze_time("2018-01-25")
spider = DetDowntownDevelopmentAuthoritySpider()
spider.settings = Settings(values={"CITY_SCRAPERS_ARCHIVE": False})

freezer.start()
parsed_items = [item for item in spider._next_meetings(test_response)]
freezer.stop()


def test_initial_request_count():
    items = list(spider.parse(test_response))
    assert len(items) == 3
    urls = {r.url for r in items if isinstance(r, scrapy.Request)}
    assert urls == {
        "http://www.degc.org/public-authorities/dda/fy-2017-2018-meetings/",
        "http://www.degc.org/public-authorities/dda/dda-fy-2016-2017-meetings/",
    }
    items = [i for i in items if not isinstance(i, scrapy.Request)]
    assert len(items) == 1


# current meeting (e.g. http://www.degc.org/public-authorities/dda/)
def test_title():
    assert parsed_items[0]["title"] == TITLE


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2018, 7, 25, 15)


def test_end():
    assert parsed_items[0]["end"] is None


def test_id():
    assert parsed_items[0]["id"] == (
        "det_downtown_development_authority/201807251500/x/board_of_directors"
    )


def test_status():
    assert parsed_items[0]["status"] == TENTATIVE


def test_location():
    assert parsed_items[0]["location"] == LOCATION


def test_source():
    assert parsed_items[0]["source"] == "http://www.degc.org/public-authorities/dda/"


def test_links():
    assert parsed_items[0]["links"] == [
        {
            "href": (
                "http://www.degc.org/wp-content/uploads"
                "/07-25-18-DDA-Board-Meeting-Agenda-Only.pdf"
            ),
            "title": "DDA Board Meeting Agenda",
        }
    ]


@pytest.mark.parametrize("item", parsed_items)
def test_all_day(item):
    assert item["all_day"] is False


@pytest.mark.parametrize("item", parsed_items)
def test_classification(item):
    assert item["classification"] == BOARD


# previous meetings e.g.
# http://www.degc.org/public-authorities/dda/dda-fy-2016-2017-meetings/
test_prev_response = file_response(
    join(dirname(__file__), "files", "det_downtown_development_authority_prev.html"),
    url="http://www.degc.org/public-authorities/dda/dda-fy-2016-2017-meetings/",
)

freezer.start()
parsed_prev_items = [item for item in spider._parse_prev_meetings(test_prev_response)]
parsed_prev_items = sorted(parsed_prev_items, key=lambda x: x["start"], reverse=True)
freezer.stop()


def test_request_count():
    freezer.start()
    requests = list(spider._prev_meetings(test_response))
    freezer.stop()
    urls = {r.url for r in requests}
    assert len(requests) == 2
    assert urls == {
        "http://www.degc.org/public-authorities/dda/fy-2017-2018-meetings/",
        "http://www.degc.org/public-authorities/dda/dda-fy-2016-2017-meetings/",
    }


def test_prev_meeting_count():
    # 2016-2017 page (15 meetings)
    assert len(parsed_prev_items) == 7


def test_prev_title():
    assert parsed_prev_items[0]["title"] == TITLE


def test_prev_description():
    assert parsed_prev_items[0]["description"] == ""


def test_prev_start():
    assert parsed_prev_items[0]["start"] == datetime(2017, 6, 28, 15)


def test_prev_end():
    assert parsed_prev_items[0]["end"] is None


def test_prev_id():
    assert parsed_prev_items[0]["id"] == (
        "det_downtown_development_authority/201706281500/x/board_of_directors"
    )


def test_prev_status():
    assert parsed_prev_items[0]["status"] == PASSED


def test_prev_location():
    assert parsed_prev_items[0]["location"] == LOCATION


def test_prev_source():
    assert parsed_prev_items[0]["source"] == (
        "http://www.degc.org/public-authorities/" "dda/dda-fy-2016-2017-meetings/"
    )


def test_prev_links():
    assert parsed_prev_items[0]["links"] == [
        {
            "href": (
                "http://www.degc.org/wp-content/uploads"
                "/2017-06-28-dda-special-board-meeting-materials.pdf"
            ),
            "title": "DDA Meeting Materials",
        },
        {
            "href": (
                "http://www.degc.org/wp-content/uploads" "/2017-06-28-Attachment-D.pdf"
            ),
            "title": "DDA Attachment D",
        },
        {
            "href": (
                "http://www.degc.org/wp-content/uploads" "/2017-06-28-Attachment-K.pdf"
            ),
            "title": "DDA Attachment k",
        },
        {
            "href": (
                "http://www.degc.org/wp-content/uploads"
                "/2017-06-28-DDA-Board-Meeting-Minutes.pdf"
            ),
            "title": "DDA Meeting Minutes",
        },
    ]


@pytest.mark.parametrize("item", parsed_prev_items)
def test_prev_all_day(item):
    assert item["all_day"] is False


@pytest.mark.parametrize("item", parsed_prev_items)
def test_prev_classification(item):
    assert item["classification"] == BOARD
