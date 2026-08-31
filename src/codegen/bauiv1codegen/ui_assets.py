# Released under the MIT License. See LICENSE for details.
#
"""Spec for the assets the ui_v1 widget layer draws itself with.

Consumed by codegen via the ``gen_ui_asset_set_py`` and
``gen_ui_asset_set_cpp`` pcommands. Adding a slot here and running
``make codegen`` regenerates the ``bauiv1.UIAssetSet`` class, the
native struct, and the unpacker between them; any side that does not
account for the new slot then fails to build.

A slot's ``default`` names ui_v1's own fallback art as an attr path
on the group's ``default_module``; it is emitted as plain attribute
access in the generated class, so a renamed asset is a type error
rather than a silent breakage. Slots without one become required
constructor args on ``UIAssetSet``. See ``batools.ui_assets`` for
the full rationale.

Not imported at runtime -- this is build-time only.
"""

from batools.ui_assets import Group, Kind, Slot, UIAssetSpec

SPEC = UIAssetSpec(
    groups=[
        Group(
            name='chrome',
            default_module='_uiv1assets',
            doc=(
                'Window furniture -- the backings, buttons,'
                ' scrollbars and widget art the ui draws itself'
                ' out of.'
            ),
            slots=[
            # ---- Textures ----
            Slot(
                name='back_icon',
                kind=Kind.TEXTURE,
                doc='Back-arrow glyph on nav buttons.',
                default='textures.back_icon',
            ),
            Slot(
                name='bomb_button',
                kind=Kind.TEXTURE,
                doc='Bomb glyph used on touch controls shown in ui.',
                default='textures.bomb_button',
            ),
            Slot(
                name='button_square',
                kind=Kind.TEXTURE,
                doc='Square button face.',
                default='textures.button_square',
            ),
            Slot(
                name='button_square_wide',
                kind=Kind.TEXTURE,
                doc='Wide square button face.',
                default='textures.button_square_wide',
            ),
            Slot(
                name='circle',
                kind=Kind.TEXTURE,
                doc='Plain filled circle.',
                default='textures.circle',
            ),
            Slot(
                name='circle_soft',
                kind=Kind.TEXTURE,
                doc='Soft-edged filled circle.',
                default='textures.circle_soft',
            ),
            Slot(
                name='glow',
                kind=Kind.TEXTURE,
                doc='Additive glow sprite.',
                default='textures.glow',
            ),
            Slot(
                name='menu_button',
                kind=Kind.TEXTURE,
                doc='Menu glyph on the root ui bar.',
                default='textures.menu_button',
            ),
            Slot(
                name='nub',
                kind=Kind.TEXTURE,
                doc='Small nub marker.',
                default='textures.nub',
            ),
            Slot(
                name='page_left_right',
                kind=Kind.TEXTURE,
                doc='Left/right page-flip arrows.',
                default='textures.page_left_right',
            ),
            Slot(
                name='scroll_widget',
                kind=Kind.TEXTURE,
                doc='Scroll-region background.',
                default='textures.scroll_widget',
            ),
            Slot(
                name='scroll_widget_glow',
                kind=Kind.TEXTURE,
                doc='Scroll-region edge glow.',
                default='textures.scroll_widget_glow',
            ),
            Slot(
                name='shadow_sharp',
                kind=Kind.TEXTURE,
                doc='Hard-edged drop shadow.',
                default='textures.shadow_sharp',
            ),
            Slot(
                name='spinner',
                kind=Kind.TEXTURE,
                doc='Busy spinner.',
                default='textures.spinner',
            ),
            Slot(
                name='spinner0',
                kind=Kind.TEXTURE,
                doc='Spinner animation frame 0.',
                default='textures.spinner0',
            ),
            Slot(
                name='spinner1',
                kind=Kind.TEXTURE,
                doc='Spinner animation frame 1.',
                default='textures.spinner1',
            ),
            Slot(
                name='spinner10',
                kind=Kind.TEXTURE,
                doc='Spinner animation frame 10.',
                default='textures.spinner10',
            ),
            Slot(
                name='spinner11',
                kind=Kind.TEXTURE,
                doc='Spinner animation frame 11.',
                default='textures.spinner11',
            ),
            Slot(
                name='spinner2',
                kind=Kind.TEXTURE,
                doc='Spinner animation frame 2.',
                default='textures.spinner2',
            ),
            Slot(
                name='spinner3',
                kind=Kind.TEXTURE,
                doc='Spinner animation frame 3.',
                default='textures.spinner3',
            ),
            Slot(
                name='spinner4',
                kind=Kind.TEXTURE,
                doc='Spinner animation frame 4.',
                default='textures.spinner4',
            ),
            Slot(
                name='spinner5',
                kind=Kind.TEXTURE,
                doc='Spinner animation frame 5.',
                default='textures.spinner5',
            ),
            Slot(
                name='spinner6',
                kind=Kind.TEXTURE,
                doc='Spinner animation frame 6.',
                default='textures.spinner6',
            ),
            Slot(
                name='spinner7',
                kind=Kind.TEXTURE,
                doc='Spinner animation frame 7.',
                default='textures.spinner7',
            ),
            Slot(
                name='spinner8',
                kind=Kind.TEXTURE,
                doc='Spinner animation frame 8.',
                default='textures.spinner8',
            ),
            Slot(
                name='spinner9',
                kind=Kind.TEXTURE,
                doc='Spinner animation frame 9.',
                default='textures.spinner9',
            ),
            Slot(
                name='start_button',
                kind=Kind.TEXTURE,
                doc='Start glyph used on touch controls shown in ui.',
                default='textures.start_button',
            ),
            Slot(
                name='text_clear_button',
                kind=Kind.TEXTURE,
                doc='Clear-text (x) glyph in text fields.',
                default='textures.text_clear_button',
            ),
            Slot(
                name='ui_atlas',
                kind=Kind.TEXTURE,
                doc='Primary ui sprite atlas.',
                default='textures.ui_atlas',
            ),
            Slot(
                name='ui_atlas2',
                kind=Kind.TEXTURE,
                doc='Secondary ui sprite atlas.',
                default='textures.ui_atlas2',
            ),
            Slot(
                name='users_button',
                kind=Kind.TEXTURE,
                doc='Squad/users glyph on the root ui bar.',
                default='textures.users_button',
            ),
            Slot(
                name='white',
                kind=Kind.TEXTURE,
                doc='Flat white pixel.',
                default='textures.white',
            ),
            Slot(
                name='window_hsmall_vmed',
                kind=Kind.TEXTURE,
                doc='Window background for taller windows.',
                default='textures.window_hsmall_vmed',
            ),
            Slot(
                name='window_hsmall_vsmall',
                kind=Kind.TEXTURE,
                doc='Window background for shorter windows.',
                default='textures.window_hsmall_vsmall',
            ),
            # ---- Meshes ----
            Slot(
                name='button_back_opaque',
                kind=Kind.MESH,
                doc='Button back backing (opaque pass).',
                default='meshes.button_back_opaque',
            ),
            Slot(
                name='button_back_small_opaque',
                kind=Kind.MESH,
                doc='Button back small backing (opaque pass).',
                default='meshes.button_back_small_opaque',
            ),
            Slot(
                name='button_back_small_transparent',
                kind=Kind.MESH,
                doc='Button back small backing (transparent pass).',
                default='meshes.button_back_small_transparent',
            ),
            Slot(
                name='button_back_transparent',
                kind=Kind.MESH,
                doc='Button back backing (transparent pass).',
                default='meshes.button_back_transparent',
            ),
            Slot(
                name='button_large_opaque',
                kind=Kind.MESH,
                doc='Button large backing (opaque pass).',
                default='meshes.button_large_opaque',
            ),
            Slot(
                name='button_large_transparent',
                kind=Kind.MESH,
                doc='Button large backing (transparent pass).',
                default='meshes.button_large_transparent',
            ),
            Slot(
                name='button_larger_opaque',
                kind=Kind.MESH,
                doc='Button larger backing (opaque pass).',
                default='meshes.button_larger_opaque',
            ),
            Slot(
                name='button_larger_transparent',
                kind=Kind.MESH,
                doc='Button larger backing (transparent pass).',
                default='meshes.button_larger_transparent',
            ),
            Slot(
                name='button_medium_opaque',
                kind=Kind.MESH,
                doc='Button medium backing (opaque pass).',
                default='meshes.button_medium_opaque',
            ),
            Slot(
                name='button_medium_transparent',
                kind=Kind.MESH,
                doc='Button medium backing (transparent pass).',
                default='meshes.button_medium_transparent',
            ),
            Slot(
                name='button_small_opaque',
                kind=Kind.MESH,
                doc='Button small backing (opaque pass).',
                default='meshes.button_small_opaque',
            ),
            Slot(
                name='button_small_transparent',
                kind=Kind.MESH,
                doc='Button small backing (transparent pass).',
                default='meshes.button_small_transparent',
            ),
            Slot(
                name='button_square_opaque',
                kind=Kind.MESH,
                doc='Button square backing (opaque pass).',
                default='meshes.button_square_opaque',
            ),
            Slot(
                name='button_square_transparent',
                kind=Kind.MESH,
                doc='Button square backing (transparent pass).',
                default='meshes.button_square_transparent',
            ),
            Slot(
                name='button_tab_opaque',
                kind=Kind.MESH,
                doc='Button tab backing (opaque pass).',
                default='meshes.button_tab_opaque',
            ),
            Slot(
                name='button_tab_transparent',
                kind=Kind.MESH,
                doc='Button tab backing (transparent pass).',
                default='meshes.button_tab_transparent',
            ),
            Slot(
                name='check_transparent',
                kind=Kind.MESH,
                doc='Checkbox tick.',
                default='meshes.check_transparent',
            ),
            Slot(
                name='image1x1',
                kind=Kind.MESH,
                doc='Unit quad for plain image draws.',
                default='meshes.image1x1',
            ),
            Slot(
                name='scroll_bar_thumb_opaque',
                kind=Kind.MESH,
                doc='Scrollbar thumb (opaque pass).',
                default='meshes.scroll_bar_thumb_opaque',
            ),
            Slot(
                name='scroll_bar_thumb_short_opaque',
                kind=Kind.MESH,
                doc='Short scrollbar thumb (opaque pass).',
                default='meshes.scroll_bar_thumb_short_opaque',
            ),
            Slot(
                name='scroll_bar_thumb_short_transparent',
                kind=Kind.MESH,
                doc='Short scrollbar thumb (transparent pass).',
                default='meshes.scroll_bar_thumb_short_transparent',
            ),
            Slot(
                name='scroll_bar_thumb_transparent',
                kind=Kind.MESH,
                doc='Scrollbar thumb (transparent pass).',
                default='meshes.scroll_bar_thumb_transparent',
            ),
            Slot(
                name='scroll_bar_trough_transparent',
                kind=Kind.MESH,
                doc='Scrollbar trough.',
                default='meshes.scroll_bar_trough_transparent',
            ),
            Slot(
                name='soft_edge_outside',
                kind=Kind.MESH,
                doc='Soft outer edge trim.',
                default='meshes.soft_edge_outside',
            ),
            Slot(
                name='text_box_transparent',
                kind=Kind.MESH,
                doc='Text-field background.',
                default='meshes.text_box_transparent',
            ),
            Slot(
                name='window_hsmall_vmed_opaque',
                kind=Kind.MESH,
                doc='Window backing mesh (opaque pass).',
                default='meshes.window_hsmall_vmed_opaque',
            ),
            Slot(
                name='window_hsmall_vmed_transparent',
                kind=Kind.MESH,
                doc='Window backing mesh (transparent pass).',
                default='meshes.window_hsmall_vmed_transparent',
            ),
            Slot(
                name='window_hsmall_vsmall_opaque',
                kind=Kind.MESH,
                doc='Window backing mesh (opaque pass).',
                default='meshes.window_hsmall_vsmall_opaque',
            ),
            Slot(
                name='window_hsmall_vsmall_transparent',
                kind=Kind.MESH,
                doc='Window backing mesh (transparent pass).',
                default='meshes.window_hsmall_vsmall_transparent',
            ),
            # ---- Sounds ----
            Slot(
                name='swish',
                kind=Kind.SOUND,
                doc='Standard widget-interaction whoosh.',
                default='audio.swish',
            ),
            Slot(
                name='swish2',
                kind=Kind.SOUND,
                doc='Button-press whoosh variant.',
                default='audio.swish2',
            ),
            Slot(
                name='swish3',
                kind=Kind.SOUND,
                doc='Button-release / checkbox whoosh variant.',
                default='audio.swish3',
            ),
            Slot(
                name='score_increase',
                kind=Kind.SOUND,
                doc='Ticker for animated count-ups (currency, rank).',
                default='audio.score_increase',
            ),
            ],
        ),
        Group(
            name='toolbar',
            doc=(
                'Art for the persistent root toolbar -- the'
                ' account, currency and menu affordances that sit'
                ' above every window.'
            ),
            slots=[
            # ---- Textures ----
            Slot(
                name='level_icon',
                kind=Kind.TEXTURE,
                doc='Level meter icon on the root ui bar.',
            ),
            Slot(
                name='trophy',
                kind=Kind.TEXTURE,
                doc='League-rank trophy on the root ui bar.',
            ),
            Slot(
                name='chest_icon_empty',
                kind=Kind.TEXTURE,
                doc='Empty chest slot on the root ui bar.',
            ),
            Slot(
                name='log_icon',
                kind=Kind.TEXTURE,
                doc='Inbox/log glyph on the root ui bar.',
            ),
            Slot(
                name='leaderboards_icon',
                kind=Kind.TEXTURE,
                doc='Leaderboards glyph on the root ui bar.',
            ),
            Slot(
                name='inventory_icon',
                kind=Kind.TEXTURE,
                doc='Inventory glyph on the root ui bar.',
            ),
            Slot(
                name='store_icon',
                kind=Kind.TEXTURE,
                doc='Store glyph on the root ui bar.',
            ),
            Slot(
                name='store_character_xmas',
                kind=Kind.TEXTURE,
                doc='Seasonal store-button decoration.',
            ),
            Slot(
                name='coin',
                kind=Kind.TEXTURE,
                doc='Coin (tickets currency) icon on the root ui bar.',
            ),
            Slot(
                name='tickets',
                kind=Kind.TEXTURE,
                doc='Tickets meter icon on the root ui bar.',
            ),
            Slot(
                name='lock',
                kind=Kind.TEXTURE,
                doc='Lock overlay on a locked chest slot.',
            ),
            Slot(
                name='tv',
                kind=Kind.TEXTURE,
                doc='Watch-ad overlay on a chest slot.',
            ),
            Slot(
                name='achievements_icon',
                kind=Kind.TEXTURE,
                doc='Achievements glyph on the root ui bar.',
            ),
            Slot(
                name='settings_icon',
                kind=Kind.TEXTURE,
                doc='Settings glyph on the root ui bar.',
            ),
            # ---- Meshes ----
            Slot(
                name='currency_meter',
                kind=Kind.MESH,
                doc='Backing for the currency meters.',
            ),
            Slot(
                name='currency_plus_button',
                kind=Kind.MESH,
                doc='Backing for the currency plus button.',
            ),
            Slot(
                name='toolbar_backing_top2',
                kind=Kind.MESH,
                doc='Top toolbar backing.',
            ),
            Slot(
                name='toolbar_backing_bottom2',
                kind=Kind.MESH,
                doc='Bottom toolbar backing.',
            ),
            ],
        ),
    ],
)
