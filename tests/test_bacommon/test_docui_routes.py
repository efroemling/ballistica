# Released under the MIT License. See LICENSE for details.
#
"""Tests for type-safe doc-ui routes and local-actions."""

import pytest

from efro.dataclassio import dataclass_to_dict

import bacommon.docui.v2 as dui2
from bacommon.langstr import LangStrSpecValue
from bacommon.docui.routes import DocUIRouteError

# Note: importing as a module since pytest tries to collect 'Test*'
# classes it finds in test module namespaces.
import bacommon.docui.routes.docuitest as rt


def test_route_wire_form() -> None:
    """Routes should encode to exactly what we used to write by hand."""

    assert rt.Root().request() == dui2.Request('/')
    assert rt.Root(test_effects=True).request() == dui2.Request(
        '/', args={'test_effects': True}
    )
    assert rt.TimedActions(val=3).request() == dui2.Request(
        '/timedactions', args={'val': 3}
    )
    assert rt.WebTestPost().request() == dui2.Request(
        '/webtest/post', method=dui2.RequestMethod.POST
    )

    browse = rt.Test2().browse()
    assert isinstance(browse, dui2.Browse)
    assert browse.request == dui2.Request('/test2')

    replace = rt.Test2().replace(default_sound=False)
    assert isinstance(replace, dui2.Replace)
    assert replace.request == dui2.Request('/test2')
    assert replace.default_sound is False


def test_route_round_trip() -> None:
    """Every route in a family should survive a trip through a request."""
    for routetype in rt.TestRoute.get_route_types():
        route = routetype()
        assert rt.TestRoute.from_request(route.request()) == route

    route2 = rt.TestRoute.from_request(rt.TimedActions(val=2).request())
    assert isinstance(route2, rt.TimedActions)
    assert route2.val == 2


def test_route_family_sanity() -> None:
    """Paths in a family must be unique."""
    paths = [t.get_path() for t in rt.TestRoute.get_route_types()]
    assert len(paths) == len(set(paths))


def test_route_errors() -> None:
    """Things that don't map to a route should say so."""

    # Unknown path.
    with pytest.raises(DocUIRouteError):
        rt.TestRoute.from_request(dui2.Request('/invalidrequest'))

    # Wrong method for a known path.
    with pytest.raises(DocUIRouteError):
        rt.TestRoute.from_request(dui2.Request('/webtest/post'))
    with pytest.raises(DocUIRouteError):
        rt.TestRoute.from_request(
            dui2.Request('/', method=dui2.RequestMethod.POST)
        )

    # Family classes are not themselves routes.
    with pytest.raises(TypeError):
        rt.TestRoute.get_path()

    # Bad arg types.
    with pytest.raises(DocUIRouteError):
        rt.TestRoute.from_request(
            dui2.Request('/timedactions', args={'val': 'notanint'})
        )


def test_local_actions() -> None:
    """Local-actions should encode/decode similarly."""

    local = rt.TestAction(testparam=123).local()
    assert isinstance(local, dui2.Local)
    assert local.immediate_local_action == 'testaction'
    assert local.immediate_local_action_args == {'testparam': 123}
    assert not local.close_window

    response = dui2.Response(page=dui2.Page(title=0, rows=[]))
    rt.TestAction(testparam=234).attach(response)
    assert response.local_action == 'testaction'
    assert response.local_action_args == {'testparam': 234}

    action = rt.TestLocalAction.from_name_and_args(
        'testaction', {'testparam': 5}
    )
    assert action == rt.TestAction(testparam=5)

    # Unknown name.
    with pytest.raises(DocUIRouteError):
        rt.TestLocalAction.from_name_and_args('nope', {})

    # Missing required arg.
    with pytest.raises(DocUIRouteError):
        rt.TestLocalAction.from_name_and_args('testaction', {})


def test_classic_store_wire_form() -> None:
    """Store routes must keep the wire keys deployed clients/servers use."""
    import bacommon.docui.routes.classicstore as sr

    assert sr.Root().request() == dui2.Request('/')
    assert sr.Root(
        debug=True, legacy_profiles=True, profiles_only=True
    ).request() == dui2.Request('/', args={'d': True, 'lp': True, 'po': True})
    assert sr.Root(unlockreqs=['a', 'b']).request() == dui2.Request(
        '/', args={'unlockreqs': ['a', 'b']}
    )
    assert sr.Purchase(purchase_id='bones').request() == dui2.Request(
        '/p', args={'i': 'bones'}
    )
    assert sr.PurchaseConfirm(
        purchase_id='bones', purchase_method=sr.PurchaseMethod.TICKETS
    ).request() == dui2.Request(
        '/pc', method=dui2.RequestMethod.POST, args={'i': 'bones', 'm': 'k'}
    )

    assert sr.ProfileEdit(profile_name='Bob').request() == dui2.Request(
        '/profile', args={'pn': 'Bob'}
    )
    assert sr.ProfileSave(profile_name='Bob').request() == dui2.Request(
        '/profile/save', method=dui2.RequestMethod.POST, args={'pn': 'Bob'}
    )
    # The editor's draft is page state, arriving on the route.
    draft = sr.ProfileDraft(
        name='Bobby', color=(1.0, 0.5, 0.0), highlight=(0.0, 0.0, 1.0)
    )
    assert draft.encode() == {
        'cl': [1.0, 0.5, 0.0],
        'h': [0.0, 0.0, 1.0],
        'n': 'Bobby',
        'c': '',
        '_t': 'classic.profile_draft',
    }
    # Colors always ride; a draft without them is no draft at all.
    assert (
        sr.ProfileDraft.decode({'n': 'Bobby', '_t': draft.get_state_id()})
        is None
    )
    route = sr.StoreRoute.from_request(
        dui2.Request(
            '/profile/save',
            method=dui2.RequestMethod.POST,
            args={'pn': 'Bob'},
            state=draft.encode(),
        )
    )
    assert isinstance(route, sr.ProfileSave)
    assert route.get_state(sr.ProfileDraft) == draft
    assert sr.ProfileDelete(profile_name='Bob').request() == dui2.Request(
        '/profile/delete', method=dui2.RequestMethod.POST, args={'pn': 'Bob'}
    )

    # Args a newer peer adds should survive a trip through a route.
    route = sr.StoreRoute.from_request(
        dui2.Request('/p', args={'i': 'bones', 'newthing': 1})
    )
    assert route.request().args == {'i': 'bones', 'newthing': 1}

    # Required args are required.
    with pytest.raises(DocUIRouteError):
        sr.StoreRoute.from_request(dui2.Request('/p'))

    assert sr.SpawnBot(name='Zoe').local().immediate_local_action_args == {
        'name': 'Zoe'
    }
    assert sr.GetTokens().local().immediate_local_action == 'get_tokens'

    for family in (sr.StoreRoute,):
        paths = [t.get_path() for t in family.get_route_types()]
        assert len(paths) == len(set(paths))


def test_shared_path_routes() -> None:
    """A path can host one route per method."""
    import bacommon.docui.routes.classicleaguepresidency as lr

    assert lr.Root(bid=50).request() == dui2.Request('/', args={'t': 50})
    assert lr.SubmitBid(bid=50).request() == dui2.Request(
        '/', method=dui2.RequestMethod.POST, args={'t': 50}
    )

    got = lr.LeaguePresidencyRoute.from_request(dui2.Request('/'))
    assert isinstance(got, lr.Root)
    got = lr.LeaguePresidencyRoute.from_request(
        dui2.Request('/', method=dui2.RequestMethod.POST, args={'t': 75})
    )
    assert isinstance(got, lr.SubmitBid) and got.bid == 75

    # Args deployed clients send that we don't otherwise care about.
    got = lr.LeaguePresidencyRoute.from_request(
        dui2.Request('/', args={'season': 'a', 't': 0, 's': False})
    )
    assert isinstance(got, lr.Root) and got.season == 'a'

    # Path + method pairs must be unique within a family.
    pairs = [
        (t.get_path(), t.get_method())
        for t in lr.LeaguePresidencyRoute.get_route_types()
    ]
    assert len(pairs) == len(set(pairs))


def test_page_state() -> None:
    """Typed page state should encode, decode and refuse strangers."""
    from bacommon.docui.routes import validate_page_state

    wstate = rt.WidgetTestState

    state = wstate(plain=True, presses=3)
    data = state.encode()
    assert data == {
        'plain': True,
        'live': False,
        'checked_disabled': True,
        'unchecked_disabled': False,
        'presses': 3,
        'text_short': '',
        'text_medium': 'Some text',
        'text_long': '',
        'text_live': '',
        'text_disabled': 'Not editable',
        'flavor': 'v',
        'flavor_live': 'v',
        'size': 'm',
        'size_long': 'm',
        # (An optional's None is a real null in the state, not an
        # absent key.)
        'topping': None,
        'difficulty': 'normal',
        'region': None,
        'flavor_disabled': 'c',
        'topping_disabled': None,
        'difficulty_disabled': 'hard',
        'region_disabled': 'eu',
        'volume': 0.5,
        'volume_disabled': 0.3,
        'series_length': 7.0,
        'series_length_disabled': 5.0,
        'tint': [0.5, 0.25, 1.0],
        'tint_disabled': [1.0, 0.6, 0.1],
        'spacing_top_demo': False,
        'spacing_bottom_demo': False,
        'bands_demo': False,
        '_t': 'docuitest.widgets',
    }
    assert wstate.decode(data) == state

    # No state, some other type's state, and junk all read as none.
    assert wstate.decode(None) is None
    assert wstate.decode({**data, '_t': 'something.else'}) is None
    assert wstate.decode({'plain': True}) is None
    assert wstate.decode({**data, 'presses': 'lots'}) is None

    # Keys and assigns come from type-checked field lookups.
    assert wstate.key(lambda s: s.live) == 'live'
    assign = wstate.assign(lambda s: s.presses, 4)
    assert (assign.key, assign.value) == ('presses', 4)
    assert wstate.get_keys() == set(data) - {'_t'}

    # State arrives with requests, by way of routes.
    route = rt.TestRoute.from_request(
        dui2.Request('/widgets', state=data, trigger='live')
    )
    assert isinstance(route, rt.Widgets)
    assert route.get_state(wstate) == state
    assert route.get_trigger() == 'live'
    assert rt.Widgets().get_state(wstate) is None

    # The route itself never carries state (a server building actions
    # from a decoded route must not pin the client's live state), but
    # the request it came from is kept for forwarding.
    assert route.request().state is None and route.request().trigger is None
    src = route.get_source_request()
    assert src is not None and src.state == data and src.trigger == 'live'
    assert rt.Widgets().get_source_request() is None

    # ...and goes out via actions.
    action = rt.Widgets().replace(sets=[assign])
    assert action.sets == {'presses': 4} and action.state is None
    assert route.replace().state is None
    action2 = rt.Widgets().browse(state=state)
    assert action2.state == data

    # Rows/sets must refer to keys of the state type the page declares.
    row = wstate.checkbox_row(lambda s: s.plain)
    assert row.name == 'plain'
    textrow = wstate.text_input_row(lambda s: s.text_short, max_chars=8)
    assert (textrow.name, textrow.max_chars) == ('text_short', 8)
    page = dui2.Page(title=0, rows=[row], state=data)
    validate_page_state(page)
    row.name = 'nope'
    with pytest.raises(ValueError):
        validate_page_state(page)
    with pytest.raises(ValueError):
        validate_page_state(dui2.Page(title=0, rows=[row]))

    # Pages with state of a type we've never heard of are left alone.
    validate_page_state(
        dui2.Page(title=0, rows=[row], state={'_t': 'third.party'})
    )


def test_choice_rows() -> None:
    """Choice rows over enums, optional enums, and string sets."""
    wstate = rt.WidgetTestState
    data = wstate().encode()

    # Choice rows enumerate the enum (in order) unless narrowed, and
    # enum values round-trip through state as their wire values.
    choicerow = wstate.choice_row(
        lambda s: s.flavor,
        choice_label=lambda f: LangStrSpecValue.literal(f.name),
    )
    assert [c.value for c in choicerow.choices] == ['v', 'c', 's', 'm']
    narrowed = wstate.choice_row(
        lambda s: s.flavor,
        choice_label=lambda f: LangStrSpecValue.literal(f.name),
        choices=[rt.Flavor.MINT, rt.Flavor.VANILLA],
    )
    assert [c.value for c in narrowed.choices] == ['m', 'v']
    assign2 = wstate.assign(lambda s: s.flavor, rt.Flavor.STRAWBERRY)
    assert assign2.value == 's'
    decoded = wstate.decode({**data, 'flavor': 's'})
    assert decoded is not None and decoded.flavor is rt.Flavor.STRAWBERRY

    # An optional enum field gets a None choice first, whose label is
    # required (and refused for a non-optional field).
    optrow = wstate.choice_row(
        lambda s: s.topping,
        choice_label=lambda f: LangStrSpecValue.literal(f.name),
        none_label=LangStrSpecValue.literal('nothing'),
        choices=[rt.Flavor.MINT],
    )
    assert [c.value for c in optrow.choices] == [None, 'm']
    # (Mypy rejects this one too; it's the runtime check under test.)
    with pytest.raises(TypeError):
        wstate.choice_row(  # type: ignore[type-var]
            lambda s: s.topping,
            choice_label=lambda f: LangStrSpecValue.literal(
                f.name  # type: ignore[union-attr]
            ),
        )
    # (This one only the runtime check catches.)
    with pytest.raises(TypeError):
        wstate.choice_row(
            lambda s: s.flavor,
            choice_label=lambda f: LangStrSpecValue.literal(f.name),
            none_label=LangStrSpecValue.literal('nothing'),
        )
    # String fields take (value, label) pairs instead of a label fn.
    lit = LangStrSpecValue.literal
    strrow = wstate.choice_row(
        lambda s: s.difficulty,
        choices=[('easy', lit('Easy')), ('hard', lit('Hard'))],
    )
    assert [c.value for c in strrow.choices] == ['easy', 'hard']
    optstrrow = wstate.choice_row(
        lambda s: s.region,
        choices=[('us', lit('US'))],
        none_label=lit('Any'),
    )
    assert [c.value for c in optstrrow.choices] == [None, 'us']
    with pytest.raises(ValueError):
        wstate.choice_row(
            lambda s: s.difficulty,
            choices=[('easy', lit('Easy')), ('easy', lit('Easy again'))],
        )
    # Disabled options are named the way choices are given (members or
    # str values), must be among the choices, and only reach the wire
    # when set.
    disrow = wstate.choice_row(
        lambda s: s.flavor,
        choice_label=lambda f: LangStrSpecValue.literal(f.name),
        disabled_choices=[rt.Flavor.MINT],
    )
    assert [c.disabled for c in disrow.choices] == [False] * 3 + [True]
    # (Disabling options leaves the row itself enabled.)
    assert not disrow.disabled
    disstrrow = wstate.choice_row(
        lambda s: s.difficulty,
        choices=[('easy', lit('Easy')), ('hard', lit('Hard'))],
        disabled_choices=['hard'],
    )
    assert [c.disabled for c in disstrrow.choices] == [False, True]
    assert 'd' not in dataclass_to_dict(disstrrow.choices[0])
    assert dataclass_to_dict(disstrrow.choices[1])['d'] is True
    with pytest.raises(ValueError):
        wstate.choice_row(
            lambda s: s.flavor,
            choice_label=lambda f: LangStrSpecValue.literal(f.name),
            choices=[rt.Flavor.VANILLA],
            disabled_choices=[rt.Flavor.MINT],
        )
    # Disabling the whole row is a separate flag, only on the wire when
    # set.
    rowdis = wstate.choice_row(
        lambda s: s.difficulty,
        choices=[('easy', lit('Easy')), ('hard', lit('Hard'))],
        disabled=True,
    )
    assert rowdis.disabled
    assert not any(c.disabled for c in rowdis.choices)
    assert dataclass_to_dict(rowdis)['dis'] is True
    assert 'dis' not in dataclass_to_dict(disstrrow)
    # (Mypy rejects these two as well; the runtime checks are under
    # test.)
    with pytest.raises(TypeError):
        wstate.choice_row(
            lambda s: s.region,  # type: ignore[arg-type, return-value]
            choices=[('us', lit('US'))],
        )
    with pytest.raises(TypeError):
        wstate.choice_row(  # type: ignore[type-var]
            lambda s: s.difficulty,
            choice_label=lambda f: lit(f.name),  # type: ignore[attr-defined]
        )
    assert wstate.assign(lambda s: s.topping, None).value is None
    assert wstate.assign(lambda s: s.topping, rt.Flavor.MINT).value == 'm'
    # (Mypy widens V to accept this; the runtime check does not.)
    with pytest.raises(TypeError):
        wstate.assign(lambda s: s.flavor, None)
    decoded = wstate.decode({**data, 'topping': None})
    assert decoded is not None and decoded.topping is None
    decoded = wstate.decode({**data, 'topping': 'c'})
    assert decoded is not None and decoded.topping is rt.Flavor.CHOCOLATE


def test_color_rows() -> None:
    """Color rows bind rgb-tuple fields; colors ride as [r, g, b]."""
    from bacommon.docui.routes import validate_page_state

    wstate = rt.WidgetTestState
    row = wstate.color_row(lambda s: s.tint)
    assert row.name == 'tint'
    assert wstate().encode()['tint'] == [0.5, 0.25, 1.0]
    assert wstate.assign(lambda s: s.tint, (1.0, 0.0, 0.0)).value == [
        1.0,
        0.0,
        0.0,
    ]
    decoded = wstate.decode({**wstate().encode(), 'tint': [0.0, 1.0, 0.0]})
    assert decoded is not None and decoded.tint == (0.0, 1.0, 0.0)
    validate_page_state(dui2.Page(title=0, rows=[row], state=wstate().encode()))
    # Only rgb-tuple fields qualify (mypy rejects this too).
    with pytest.raises(TypeError):
        wstate.color_row(
            lambda s: s.difficulty  # type: ignore[arg-type, return-value]
        )


def test_presidency_state() -> None:
    """The bid rides as state for new clients and as an arg for old."""
    import bacommon.docui.routes.classicleaguepresidency as lr

    state = lr.BidState(bid=500)
    route = lr.LeaguePresidencyRoute.from_request(
        dui2.Request('/', args={'t': 0}, state=state.encode())
    )
    assert isinstance(route, lr.Root)
    assert route.bid == 0 and route.get_state(lr.BidState) == state
    action = lr.Root().replace(sets=[lr.BidState.assign(lambda s: s.bid, 510)])
    assert action.sets == {'t': 510}


def test_slider_rows() -> None:
    """Slider rows bind float fields; on_drag is local-only."""
    from bacommon.docui.routes import validate_page_state

    wstate = rt.WidgetTestState
    row = wstate.slider_row(
        lambda s: s.volume,
        min_value=0.0,
        max_value=1.0,
        increment=0.05,
        on_drag=rt.ShowVolume().local(),
        on_change=rt.Widgets().replace(),
    )
    assert row.name == 'volume' and row.on_drag is not None
    assert row.on_drag.immediate_local_action == 'showvolume'
    assert wstate().encode()['volume'] == 0.5
    validate_page_state(dui2.Page(title=0, rows=[row], state=wstate().encode()))
    # Only float fields qualify (mypy rejects this too), and the range
    # must make sense.
    with pytest.raises(TypeError):
        wstate.slider_row(
            lambda s: s.difficulty,  # type: ignore[arg-type, return-value]
            min_value=0.0,
            max_value=1.0,
            increment=0.1,
        )
    with pytest.raises(ValueError):
        wstate.slider_row(
            lambda s: s.volume, min_value=1.0, max_value=0.0, increment=0.1
        )
