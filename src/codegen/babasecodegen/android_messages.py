# Released under the MIT License. See LICENSE for details.
#
"""Typed Java<->C++ Android message specs.

Consumed by codegen via the ``gen_android_message_java`` and
``gen_android_message_cpp`` pcommands. Adding a new message here
and running ``make codegen`` regenerates bindings + abstract handler
base classes on both sides; any side that fails to implement the
new handler method is a compile error.

Not imported at runtime on either side — this is build-time only.

Type definitions (``Dir``, ``Field``, ``Message``, token constants)
live in ``tools/batools/android_messages.py`` rather than here so
that spinoff projects which omit the ``base`` featureset still
type-check the codegen module cleanly, and so this spec module
is self-typecheckable in spinoff projects (public bombsquad,
etc.) which don't have ``tools/batoolsinternal/``. See
``docs/design/spinoff.md`` for the rationale.
"""

from batools.android_messages import (
    BOOL,
    Dir,
    Field,
    FLOAT,
    INT,
    Message,
    STR,
    STR_LIST,
)

MESSAGES: list[Message] = [
    # ---- Java -> Native ----
    Message(
        name='BackPress',
        direction=Dir.JAVA_TO_NATIVE,
        doc='User pressed the Android back button.',
    ),
    Message(
        name='MainThreadCall',
        direction=Dir.JAVA_TO_NATIVE,
        fields=[Field('call_id', INT)],
        doc='Run a previously-registered call by id on the C++ main thread.',
    ),
    Message(
        name='ScreenMessage',
        direction=Dir.JAVA_TO_NATIVE,
        fields=[
            Field('text', STR),
            Field('r', FLOAT),
            Field('g', FLOAT),
            Field('b', FLOAT),
        ],
        doc='Display a colored screen message via the engine.',
    ),
    Message(
        name='InputDeviceEvent',
        direction=Dir.JAVA_TO_NATIVE,
        fields=[
            Field('m_type', INT),
            Field('joy_id', INT),
            Field('i_val', INT),
            Field('f_val', FLOAT),
            Field('s_val', STR),
        ],
        doc='Keyboard/joystick lifecycle and button events from Android.',
    ),
    Message(
        name='KeyDownEvent',
        direction=Dir.JAVA_TO_NATIVE,
        fields=[Field('keycode', INT)],
        doc='Hardware key down event (Android keycode).',
    ),
    Message(
        name='KeyUpEvent',
        direction=Dir.JAVA_TO_NATIVE,
        fields=[Field('keycode', INT)],
        doc='Hardware key up event (Android keycode).',
    ),
    Message(
        name='NetAvailChanged',
        direction=Dir.JAVA_TO_NATIVE,
        fields=[Field('available', BOOL)],
        doc='ConnectivityManager network availability changed.',
    ),
    Message(
        name='SetRunning',
        direction=Dir.JAVA_TO_NATIVE,
        fields=[Field('running', BOOL)],
        doc='Java lifecycle pause/resume signal (engine suspend/unsuspend).',
    ),
    Message(
        name='SetActive',
        direction=Dir.JAVA_TO_NATIVE,
        fields=[Field('active', BOOL)],
        doc='Java app foreground/background activity signal.',
    ),
    Message(
        name='GyroEvent',
        direction=Dir.JAVA_TO_NATIVE,
        fields=[
            Field('x', FLOAT),
            Field('y', FLOAT),
            Field('z', FLOAT),
        ],
        doc='Gyroscope sensor reading (orientation-corrected by Java).',
    ),
    Message(
        name='ResetAppState',
        direction=Dir.JAVA_TO_NATIVE,
        doc='Reset the engine to the main menu (if bootstrap is complete).',
    ),
    Message(
        name='StringEditorCancel',
        direction=Dir.JAVA_TO_NATIVE,
        doc='User dismissed the in-game string editor dialog.',
    ),
    Message(
        name='StringEditorApply',
        direction=Dir.JAVA_TO_NATIVE,
        fields=[Field('value', STR)],
        doc='User accepted edits in the in-game string editor dialog.',
    ),
    Message(
        name='AwardAdTickets',
        direction=Dir.JAVA_TO_NATIVE,
        doc='Award the user tickets for watching an ad.',
    ),
    Message(
        name='AwardAdTournamentEntry',
        direction=Dir.JAVA_TO_NATIVE,
        doc='Award the user a tournament entry for watching an ad.',
    ),
    Message(
        name='AdViewComplete',
        direction=Dir.JAVA_TO_NATIVE,
        fields=[
            Field('network', STR),
            Field('actually_watched', BOOL),
        ],
        doc='Ad view finished; report network and whether it actually played.',
    ),
    Message(
        name='DisplayUrlString',
        direction=Dir.JAVA_TO_NATIVE,
        fields=[Field('url', STR)],
        doc='Java passes a URL to native for in-game display.',
    ),
    Message(
        name='MusicPlayFailed',
        direction=Dir.JAVA_TO_NATIVE,
        fields=[Field('filename', STR)],
        doc='MediaPlayer failed to play a track; show the user an error.',
    ),
    Message(
        name='MemoryWarning',
        direction=Dir.JAVA_TO_NATIVE,
        fields=[Field('level', STR)],
        doc='Android low-memory callback; level is LOW/MEDIUM/HIGH.',
    ),
    Message(
        name='SetLaunchVls',
        direction=Dir.JAVA_TO_NATIVE,
        fields=[Field('value', STR)],
        doc='Launch verification load store payload (used for root detection).',
    ),
    Message(
        name='VScroll',
        direction=Dir.JAVA_TO_NATIVE,
        fields=[Field('amount', FLOAT)],
        doc='Vertical mouse-wheel scroll event.',
    ),
    Message(
        name='HScroll',
        direction=Dir.JAVA_TO_NATIVE,
        fields=[Field('amount', FLOAT)],
        doc='Horizontal mouse-wheel scroll event.',
    ),
    Message(
        name='SetNativeRes',
        direction=Dir.JAVA_TO_NATIVE,
        fields=[
            Field('width', INT),
            Field('height', INT),
        ],
        doc='Reported native resolution from the Android surface.',
    ),
    Message(
        name='Log',
        direction=Dir.JAVA_TO_NATIVE,
        fields=[
            Field('level', STR),
            Field('message', STR),
        ],
        doc='Java log event for routing through the engine log pipeline.',
    ),
    # ---- Java -> Native (flavor-specific senders) ----
    Message(
        name='NotLoggedInError',
        direction=Dir.JAVA_TO_NATIVE,
        doc='Show the "not signed in" screen message.',
    ),
    Message(
        name='RejectingInviteAlreadyInPartyMessage',
        direction=Dir.JAVA_TO_NATIVE,
        doc='Show the "already in party; rejecting invite" message.',
    ),
    Message(
        name='ConnectionFailedMessage',
        direction=Dir.JAVA_TO_NATIVE,
        doc='Show the generic connection-failed message.',
    ),
    Message(
        name='TemporarilyUnavailableMessage',
        direction=Dir.JAVA_TO_NATIVE,
        doc='Show the "temporarily unavailable" message.',
    ),
    Message(
        name='InProgressMessage',
        direction=Dir.JAVA_TO_NATIVE,
        doc='Show the "in progress" message.',
    ),
    Message(
        name='ErrorMessage',
        direction=Dir.JAVA_TO_NATIVE,
        doc='Show the generic error screen message.',
    ),
    Message(
        name='PurchaseNotValidError',
        direction=Dir.JAVA_TO_NATIVE,
        doc='Show the "purchase not valid" error message.',
    ),
    Message(
        name='PurchaseAlreadyInProgressError',
        direction=Dir.JAVA_TO_NATIVE,
        doc='Show the "purchase already in progress" error message.',
    ),
    Message(
        name='CardboardRingPull',
        direction=Dir.JAVA_TO_NATIVE,
        doc='Cardboard VR ring pull (orientation reset).',
    ),
    Message(
        name='GooglePlayPurchasesNotAvailableMessage',
        direction=Dir.JAVA_TO_NATIVE,
        doc='Show the "Google Play purchases not available" message.',
    ),
    Message(
        name='GooglePlayServicesNotAvailableMessage',
        direction=Dir.JAVA_TO_NATIVE,
        doc='Show the "Google Play services not available" message.',
    ),
    Message(
        name='KeepAudioWhenInactiveHint',
        direction=Dir.JAVA_TO_NATIVE,
        doc='Hint the engine to keep audio running while inactive.',
    ),
    Message(
        name='AchievementList',
        direction=Dir.JAVA_TO_NATIVE,
        fields=[Field('achievements', STR_LIST)],
        doc='Unlocked-achievement IDs reported by the Java side.',
    ),
    Message(
        name='InvitationsSentMessage',
        direction=Dir.JAVA_TO_NATIVE,
        fields=[Field('count', STR)],
        doc='Show "invitation(s) sent". Count "1" picks the singular form.',
    ),
    Message(
        name='SubmitAnalyticsCountsResponse',
        direction=Dir.JAVA_TO_NATIVE,
        fields=[Field('json', STR)],
        doc='Java side returns submit-analytics-counts payload.',
    ),
    Message(
        name='DeepLink',
        direction=Dir.JAVA_TO_NATIVE,
        fields=[Field('url', STR)],
        doc='Java passes a deep-link URL to the engine.',
    ),
    Message(
        name='HaveIncentivizedAd',
        direction=Dir.JAVA_TO_NATIVE,
        fields=[Field('available', BOOL)],
        doc='Set whether an incentivized ad is available to show.',
    ),
    Message(
        name='SetLastAdNetwork',
        direction=Dir.JAVA_TO_NATIVE,
        fields=[Field('network', STR)],
        doc='Record the most recent ad network name.',
    ),
    Message(
        name='ProductPrice',
        direction=Dir.JAVA_TO_NATIVE,
        fields=[
            Field('product_id', STR),
            Field('price', STR),
        ],
        doc='Update the displayed price for an in-app product.',
    ),
    Message(
        name='SetAccountToken',
        direction=Dir.JAVA_TO_NATIVE,
        fields=[
            Field('token_type', STR),
            Field('token_value', STR),
        ],
        doc='Java provides an updated v1 account token.',
    ),
    Message(
        name='PurchaseTransaction',
        direction=Dir.JAVA_TO_NATIVE,
        fields=[
            Field('item', STR),
            Field('receipt', STR),
            Field('signature', STR),
            Field('order_id', STR),
            Field('user_initiated', BOOL),
        ],
        doc='A purchase transaction completed (or failed) on the Java side.',
    ),
    Message(
        name='LoginAdapterGetSignInTokenResponse',
        direction=Dir.JAVA_TO_NATIVE,
        fields=[
            Field('login_type', STR),
            Field('attempt_id', STR),
            Field('result', STR),
        ],
        doc='Java responds to a login-adapter sign-in token request.',
    ),
    Message(
        name='FriendAccountList',
        direction=Dir.JAVA_TO_NATIVE,
        fields=[Field('accounts', STR_LIST)],
        doc='List of friend account ids (or names) from the Java side.',
    ),
    Message(
        name='ImplicitSignIn',
        direction=Dir.JAVA_TO_NATIVE,
        fields=[
            Field('login_type', STR),
            Field('login_id', STR),
            Field('name', STR),
        ],
        doc='Java reports an implicit (auto) sign-in.',
    ),
    Message(
        name='ImplicitLogout',
        direction=Dir.JAVA_TO_NATIVE,
        fields=[Field('login_type', STR)],
        doc='Java reports an implicit sign-out.',
    ),
    # ---- Native -> Java ----
    Message(
        name='RunMainThreadCall',
        direction=Dir.NATIVE_TO_JAVA,
        fields=[Field('call_id', INT)],
        doc=(
            'Ask Java to schedule a main-thread call by id; the Java side '
            'sends MainThreadCall back to dispatch it on the C++ main thread.'
        ),
    ),
    Message(
        name='MusicPlay',
        direction=Dir.NATIVE_TO_JAVA,
        fields=[Field('filename', STR)],
        doc='Begin playback of the named music asset.',
    ),
    Message(
        name='MusicPlayMultiple',
        direction=Dir.NATIVE_TO_JAVA,
        fields=[Field('filenames', STR_LIST)],
        doc='Begin playback of an ordered list of music asset filenames.',
    ),
    Message(
        name='MusicStop',
        direction=Dir.NATIVE_TO_JAVA,
        doc='Stop the music player (preserving its prepared state).',
    ),
    Message(
        name='MusicShutdown',
        direction=Dir.NATIVE_TO_JAVA,
        doc='Tear down the music player entirely.',
    ),
    Message(
        name='MusicSetVolume',
        direction=Dir.NATIVE_TO_JAVA,
        fields=[Field('volume', FLOAT)],
        doc='Set music player volume in [0, 1].',
    ),
    Message(
        name='SignIn',
        direction=Dir.NATIVE_TO_JAVA,
        doc='Ask the Java side to start the v1 sign-in flow.',
    ),
    Message(
        name='SignOut',
        direction=Dir.NATIVE_TO_JAVA,
        doc='Ask the Java side to sign out of the v1 account.',
    ),
    Message(
        name='SubmitAnalyticsCounts',
        direction=Dir.NATIVE_TO_JAVA,
        doc='Submit accumulated analytics counts.',
    ),
    Message(
        name='RequestStoragePermission',
        direction=Dir.NATIVE_TO_JAVA,
        doc='Request runtime WRITE_EXTERNAL_STORAGE permission.',
    ),
    Message(
        name='CrashlyticsNonFatalError',
        direction=Dir.NATIVE_TO_JAVA,
        doc='Report a non-fatal error to Crashlytics (if hooked up).',
    ),
    Message(
        name='V1LoginDidChange',
        direction=Dir.NATIVE_TO_JAVA,
        fields=[Field('login_id', STR)],
        doc='V1 login state changed; empty login_id means signed out.',
    ),
    Message(
        name='SetRes',
        direction=Dir.NATIVE_TO_JAVA,
        fields=[Field('resolution', STR)],
        doc='Java sets render resolution from a "WIDTHxHEIGHT" string.',
    ),
    Message(
        name='SetAnalyticsScreen',
        direction=Dir.NATIVE_TO_JAVA,
        fields=[Field('screen', STR)],
        doc='Set the current analytics screen name.',
    ),
    Message(
        name='AndroidMiscReadVals',
        direction=Dir.NATIVE_TO_JAVA,
        fields=[Field('json', STR)],
        doc='Set the Java miscellaneous-read-values JSON blob.',
    ),
    Message(
        name='ShowAd',
        direction=Dir.NATIVE_TO_JAVA,
        fields=[Field('purpose', STR)],
        doc='Show an ad with the given purpose tag.',
    ),
    Message(
        name='FatalErrorMessage',
        direction=Dir.NATIVE_TO_JAVA,
        fields=[Field('message', STR)],
        doc='Show a fatal error message to the user.',
    ),
    Message(
        name='IncrementAnalyticsCount',
        direction=Dir.NATIVE_TO_JAVA,
        fields=[
            Field('name', STR),
            Field('increment', INT),
        ],
        doc='Bump a Java-side analytics counter by `increment`.',
    ),
    Message(
        name='IncrementAnalyticsCountRaw',
        direction=Dir.NATIVE_TO_JAVA,
        fields=[
            Field('name', STR),
            Field('increment', INT),
        ],
        doc='Raw Google Play Player Analytics counter increment.',
    ),
    Message(
        name='IncrementAnalyticsCountRaw2',
        direction=Dir.NATIVE_TO_JAVA,
        fields=[
            Field('name', STR),
            Field('uses_increment', BOOL),
            Field('increment', INT),
        ],
        doc='Raw Google Play Player Analytics counter increment (2-arg form).',
    ),
    # ---- Native -> Java (flavor-specific actions) ----
    Message(
        name='ShowLeaderboards',
        direction=Dir.NATIVE_TO_JAVA,
        doc='Show the Play Games leaderboards UI (Google flavor).',
    ),
    Message(
        name='ShowAchievements',
        direction=Dir.NATIVE_TO_JAVA,
        doc='Show the Play Games achievements UI (Google flavor).',
    ),
    Message(
        name='ShowGameService',
        direction=Dir.NATIVE_TO_JAVA,
        doc='Show the Play Games game-service UI (Google flavor).',
    ),
    Message(
        name='ShowLeaderboard',
        direction=Dir.NATIVE_TO_JAVA,
        fields=[Field('leaderboard_id', STR)],
        doc='Show a specific Play Games leaderboard (Google flavor).',
    ),
    Message(
        name='SubmitAchievement',
        direction=Dir.NATIVE_TO_JAVA,
        fields=[Field('achievement_id', STR)],
        doc='Submit a Play Games achievement unlock (Google flavor).',
    ),
    Message(
        name='SubmitScore',
        direction=Dir.NATIVE_TO_JAVA,
        fields=[
            Field('leaderboard_id', STR),
            Field('score', INT),
        ],
        doc='Submit a score to a Play Games leaderboard (Google flavor).',
    ),
    Message(
        name='MoveTaskToBack',
        direction=Dir.NATIVE_TO_JAVA,
        doc='Ask Android to background our activity (back-quit path).',
    ),
    Message(
        name='ReviewRequest',
        direction=Dir.NATIVE_TO_JAVA,
        doc='Ask the Java side to prompt for an in-app review.',
    ),
    Message(
        name='Purchase',
        direction=Dir.NATIVE_TO_JAVA,
        fields=[Field('item', STR)],
        doc='Begin an in-app purchase flow for an item id.',
    ),
    Message(
        name='PurchaseAck',
        direction=Dir.NATIVE_TO_JAVA,
        fields=[
            Field('purchase', STR),
            Field('order_id', STR),
        ],
        doc='Acknowledge a successful purchase to the Java IAP layer.',
    ),
    Message(
        name='SetGvrRenderTargetScale',
        direction=Dir.NATIVE_TO_JAVA,
        fields=[Field('scale', FLOAT)],
        doc='Set Google VR render-target scale (Cardboard flavor).',
    ),
    Message(
        name='LoginAdapterGetSignInToken',
        direction=Dir.NATIVE_TO_JAVA,
        fields=[
            Field('login_type', STR),
            Field('attempt_id', INT),
        ],
        doc='Ask the Java side for a sign-in token for a login adapter.',
    ),
    Message(
        name='LoginAdapterBackEndActiveChange',
        direction=Dir.NATIVE_TO_JAVA,
        fields=[
            Field('login_type', STR),
            Field('active', BOOL),
        ],
        doc='Notify Java that a login adapter back-end active state changed.',
    ),
]
