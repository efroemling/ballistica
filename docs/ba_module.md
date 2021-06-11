<!-- THIS FILE IS AUTO GENERATED; DO NOT EDIT BY HAND -->
<h4><em>last updated on 2021-06-11 for Ballistica version 1.6.4 build 20378</em></h4>
<p>This page documents the Python classes and functions in the 'ba' module,
 which are the ones most relevant to modding in Ballistica. If you come across something you feel should be included here or could be better explained, please <a href="mailto:support@froemling.net">let me know</a>. Happy modding!</p>
<hr>
<h2>Table of Contents</h2>
<h4><a name="class_category_Gameplay_Classes">Gameplay Classes</a></h4>
<ul>
   <li><a href="#class_ba_Activity">ba.Activity</a></li>
   <ul>
      <li><a href="#class_ba_GameActivity">ba.GameActivity</a></li>
      <ul>
         <li><a href="#class_ba_CoopGameActivity">ba.CoopGameActivity</a></li>
         <li><a href="#class_ba_TeamGameActivity">ba.TeamGameActivity</a></li>
      </ul>
   </ul>
   <li><a href="#class_ba_Actor">ba.Actor</a></li>
   <ul>
      <li><a href="#class_ba_Map">ba.Map</a></li>
      <li><a href="#class_ba_NodeActor">ba.NodeActor</a></li>
   </ul>
   <li><a href="#class_ba_Chooser">ba.Chooser</a></li>
   <li><a href="#class_ba_Collision">ba.Collision</a></li>
   <li><a href="#class_ba_GameResults">ba.GameResults</a></li>
   <li><a href="#class_ba_GameTip">ba.GameTip</a></li>
   <li><a href="#class_ba_InputDevice">ba.InputDevice</a></li>
   <li><a href="#class_ba_Level">ba.Level</a></li>
   <li><a href="#class_ba_Lobby">ba.Lobby</a></li>
   <li><a href="#class_ba_Material">ba.Material</a></li>
   <li><a href="#class_ba_Node">ba.Node</a></li>
   <li><a href="#class_ba_Player">ba.Player</a></li>
   <ul>
      <li><a href="#class_ba_EmptyPlayer">ba.EmptyPlayer</a></li>
   </ul>
   <li><a href="#class_ba_PlayerInfo">ba.PlayerInfo</a></li>
   <li><a href="#class_ba_PlayerRecord">ba.PlayerRecord</a></li>
   <li><a href="#class_ba_ScoreConfig">ba.ScoreConfig</a></li>
   <li><a href="#class_ba_Session">ba.Session</a></li>
   <ul>
      <li><a href="#class_ba_CoopSession">ba.CoopSession</a></li>
      <li><a href="#class_ba_MultiTeamSession">ba.MultiTeamSession</a></li>
      <ul>
         <li><a href="#class_ba_DualTeamSession">ba.DualTeamSession</a></li>
         <li><a href="#class_ba_FreeForAllSession">ba.FreeForAllSession</a></li>
      </ul>
   </ul>
   <li><a href="#class_ba_SessionPlayer">ba.SessionPlayer</a></li>
   <li><a href="#class_ba_SessionTeam">ba.SessionTeam</a></li>
   <li><a href="#class_ba_Setting">ba.Setting</a></li>
   <li><a href="#class_ba_StandLocation">ba.StandLocation</a></li>
   <li><a href="#class_ba_Stats">ba.Stats</a></li>
   <li><a href="#class_ba_Team">ba.Team</a></li>
   <ul>
      <li><a href="#class_ba_EmptyTeam">ba.EmptyTeam</a></li>
   </ul>
</ul>
<h4><a name="function_category_Gameplay_Functions">Gameplay Functions</a></h4>
<ul>
   <li><a href="#function_ba_animate">ba.animate()</a></li>
   <li><a href="#function_ba_animate_array">ba.animate_array()</a></li>
   <li><a href="#function_ba_cameraflash">ba.cameraflash()</a></li>
   <li><a href="#function_ba_camerashake">ba.camerashake()</a></li>
   <li><a href="#function_ba_emitfx">ba.emitfx()</a></li>
   <li><a href="#function_ba_existing">ba.existing()</a></li>
   <li><a href="#function_ba_getactivity">ba.getactivity()</a></li>
   <li><a href="#function_ba_getcollision">ba.getcollision()</a></li>
   <li><a href="#function_ba_getnodes">ba.getnodes()</a></li>
   <li><a href="#function_ba_getsession">ba.getsession()</a></li>
   <li><a href="#function_ba_newnode">ba.newnode()</a></li>
   <li><a href="#function_ba_playsound">ba.playsound()</a></li>
   <li><a href="#function_ba_printnodes">ba.printnodes()</a></li>
   <li><a href="#function_ba_setmusic">ba.setmusic()</a></li>
   <li><a href="#function_ba_show_damage_count">ba.show_damage_count()</a></li>
</ul>
<h4><a name="class_category_General_Utility_Classes">General Utility Classes</a></h4>
<ul>
   <li><a href="#class_ba_Call">ba.Call</a></li>
   <li><a href="#class_ba_Context">ba.Context</a></li>
   <li><a href="#class_ba_ContextCall">ba.ContextCall</a></li>
   <li><a href="#class_ba_Lstr">ba.Lstr</a></li>
   <li><a href="#class_ba_Timer">ba.Timer</a></li>
   <li><a href="#class_ba_Vec3">ba.Vec3</a></li>
   <li><a href="#class_ba_WeakCall">ba.WeakCall</a></li>
</ul>
<h4><a name="function_category_General_Utility_Functions">General Utility Functions</a></h4>
<ul>
   <li><a href="#function_ba_charstr">ba.charstr()</a></li>
   <li><a href="#function_ba_clipboard_get_text">ba.clipboard_get_text()</a></li>
   <li><a href="#function_ba_clipboard_has_text">ba.clipboard_has_text()</a></li>
   <li><a href="#function_ba_clipboard_is_supported">ba.clipboard_is_supported()</a></li>
   <li><a href="#function_ba_clipboard_set_text">ba.clipboard_set_text()</a></li>
   <li><a href="#function_ba_do_once">ba.do_once()</a></li>
   <li><a href="#function_ba_garbage_collect">ba.garbage_collect()</a></li>
   <li><a href="#function_ba_getclass">ba.getclass()</a></li>
   <li><a href="#function_ba_is_browser_likely_available">ba.is_browser_likely_available()</a></li>
   <li><a href="#function_ba_is_point_in_box">ba.is_point_in_box()</a></li>
   <li><a href="#function_ba_log">ba.log()</a></li>
   <li><a href="#function_ba_newactivity">ba.newactivity()</a></li>
   <li><a href="#function_ba_normalized_color">ba.normalized_color()</a></li>
   <li><a href="#function_ba_open_url">ba.open_url()</a></li>
   <li><a href="#function_ba_print_error">ba.print_error()</a></li>
   <li><a href="#function_ba_print_exception">ba.print_exception()</a></li>
   <li><a href="#function_ba_printobjects">ba.printobjects()</a></li>
   <li><a href="#function_ba_pushcall">ba.pushcall()</a></li>
   <li><a href="#function_ba_quit">ba.quit()</a></li>
   <li><a href="#function_ba_safecolor">ba.safecolor()</a></li>
   <li><a href="#function_ba_screenmessage">ba.screenmessage()</a></li>
   <li><a href="#function_ba_set_analytics_screen">ba.set_analytics_screen()</a></li>
   <li><a href="#function_ba_storagename">ba.storagename()</a></li>
   <li><a href="#function_ba_time">ba.time()</a></li>
   <li><a href="#function_ba_timer">ba.timer()</a></li>
   <li><a href="#function_ba_timestring">ba.timestring()</a></li>
   <li><a href="#function_ba_vec3validate">ba.vec3validate()</a></li>
   <li><a href="#function_ba_verify_object_death">ba.verify_object_death()</a></li>
</ul>
<h4><a name="class_category_Asset_Classes">Asset Classes</a></h4>
<ul>
   <li><a href="#class_ba_AssetPackage">ba.AssetPackage</a></li>
   <li><a href="#class_ba_CollideModel">ba.CollideModel</a></li>
   <li><a href="#class_ba_Data">ba.Data</a></li>
   <li><a href="#class_ba_Model">ba.Model</a></li>
   <li><a href="#class_ba_Sound">ba.Sound</a></li>
   <li><a href="#class_ba_Texture">ba.Texture</a></li>
</ul>
<h4><a name="function_category_Asset_Functions">Asset Functions</a></h4>
<ul>
   <li><a href="#function_ba_getcollidemodel">ba.getcollidemodel()</a></li>
   <li><a href="#function_ba_getmaps">ba.getmaps()</a></li>
   <li><a href="#function_ba_getmodel">ba.getmodel()</a></li>
   <li><a href="#function_ba_getsound">ba.getsound()</a></li>
   <li><a href="#function_ba_gettexture">ba.gettexture()</a></li>
</ul>
<h4><a name="class_category_Message_Classes">Message Classes</a></h4>
<ul>
   <li><a href="#class_ba_CelebrateMessage">ba.CelebrateMessage</a></li>
   <li><a href="#class_ba_DieMessage">ba.DieMessage</a></li>
   <li><a href="#class_ba_DropMessage">ba.DropMessage</a></li>
   <li><a href="#class_ba_DroppedMessage">ba.DroppedMessage</a></li>
   <li><a href="#class_ba_FreezeMessage">ba.FreezeMessage</a></li>
   <li><a href="#class_ba_HitMessage">ba.HitMessage</a></li>
   <li><a href="#class_ba_ImpactDamageMessage">ba.ImpactDamageMessage</a></li>
   <li><a href="#class_ba_OutOfBoundsMessage">ba.OutOfBoundsMessage</a></li>
   <li><a href="#class_ba_PickedUpMessage">ba.PickedUpMessage</a></li>
   <li><a href="#class_ba_PickUpMessage">ba.PickUpMessage</a></li>
   <li><a href="#class_ba_PlayerDiedMessage">ba.PlayerDiedMessage</a></li>
   <li><a href="#class_ba_PlayerScoredMessage">ba.PlayerScoredMessage</a></li>
   <li><a href="#class_ba_PowerupAcceptMessage">ba.PowerupAcceptMessage</a></li>
   <li><a href="#class_ba_PowerupMessage">ba.PowerupMessage</a></li>
   <li><a href="#class_ba_ShouldShatterMessage">ba.ShouldShatterMessage</a></li>
   <li><a href="#class_ba_StandMessage">ba.StandMessage</a></li>
   <li><a href="#class_ba_ThawMessage">ba.ThawMessage</a></li>
</ul>
<h4><a name="class_category_App_Classes">App Classes</a></h4>
<ul>
   <li><a href="#class_ba_Achievement">ba.Achievement</a></li>
   <li><a href="#class_ba_AchievementSubsystem">ba.AchievementSubsystem</a></li>
   <li><a href="#class_ba_App">ba.App</a></li>
   <li><a href="#class_ba_AppConfig">ba.AppConfig</a></li>
   <li><a href="#class_ba_AppDelegate">ba.AppDelegate</a></li>
   <li><a href="#class_ba_Campaign">ba.Campaign</a></li>
   <li><a href="#class_ba_Keyboard">ba.Keyboard</a></li>
   <li><a href="#class_ba_LanguageSubsystem">ba.LanguageSubsystem</a></li>
   <li><a href="#class_ba_MetadataSubsystem">ba.MetadataSubsystem</a></li>
   <li><a href="#class_ba_MusicPlayer">ba.MusicPlayer</a></li>
   <li><a href="#class_ba_MusicSubsystem">ba.MusicSubsystem</a></li>
   <li><a href="#class_ba_Plugin">ba.Plugin</a></li>
   <li><a href="#class_ba_PluginSubsystem">ba.PluginSubsystem</a></li>
   <li><a href="#class_ba_PotentialPlugin">ba.PotentialPlugin</a></li>
   <li><a href="#class_ba_ServerController">ba.ServerController</a></li>
   <li><a href="#class_ba_UISubsystem">ba.UISubsystem</a></li>
</ul>
<h4><a name="class_category_User_Interface_Classes">User Interface Classes</a></h4>
<ul>
   <li><a href="#class_ba_UIController">ba.UIController</a></li>
   <li><a href="#class_ba_Widget">ba.Widget</a></li>
   <li><a href="#class_ba_Window">ba.Window</a></li>
</ul>
<h4><a name="function_category_User_Interface_Functions">User Interface Functions</a></h4>
<ul>
   <li><a href="#function_ba_buttonwidget">ba.buttonwidget()</a></li>
   <li><a href="#function_ba_checkboxwidget">ba.checkboxwidget()</a></li>
   <li><a href="#function_ba_columnwidget">ba.columnwidget()</a></li>
   <li><a href="#function_ba_containerwidget">ba.containerwidget()</a></li>
   <li><a href="#function_ba_hscrollwidget">ba.hscrollwidget()</a></li>
   <li><a href="#function_ba_imagewidget">ba.imagewidget()</a></li>
   <li><a href="#function_ba_rowwidget">ba.rowwidget()</a></li>
   <li><a href="#function_ba_scrollwidget">ba.scrollwidget()</a></li>
   <li><a href="#function_ba_textwidget">ba.textwidget()</a></li>
   <li><a href="#function_ba_uicleanupcheck">ba.uicleanupcheck()</a></li>
   <li><a href="#function_ba_widget">ba.widget()</a></li>
</ul>
<h4><a name="class_category_Dependency_Classes">Dependency Classes</a></h4>
<ul>
   <li><a href="#class_ba_Dependency">ba.Dependency</a></li>
   <li><a href="#class_ba_DependencyComponent">ba.DependencyComponent</a></li>
   <li><a href="#class_ba_DependencySet">ba.DependencySet</a></li>
</ul>
<h4><a name="class_category_Enums">Enums</a></h4>
<ul>
   <li><a href="#class_ba_DeathType">ba.DeathType</a></li>
   <li><a href="#class_ba_InputType">ba.InputType</a></li>
   <li><a href="#class_ba_MusicPlayMode">ba.MusicPlayMode</a></li>
   <li><a href="#class_ba_MusicType">ba.MusicType</a></li>
   <li><a href="#class_ba_Permission">ba.Permission</a></li>
   <li><a href="#class_ba_ScoreType">ba.ScoreType</a></li>
   <li><a href="#class_ba_SpecialChar">ba.SpecialChar</a></li>
   <li><a href="#class_ba_TimeFormat">ba.TimeFormat</a></li>
   <li><a href="#class_ba_TimeType">ba.TimeType</a></li>
   <li><a href="#class_ba_UIScale">ba.UIScale</a></li>
</ul>
<h4><a name="class_category_Exception_Classes">Exception Classes</a></h4>
<ul>
   <li><a href="#class_ba_ContextError">ba.ContextError</a></li>
   <li><a href="#class_ba_DependencyError">ba.DependencyError</a></li>
   <li><a href="#class_ba_NotFoundError">ba.NotFoundError</a></li>
   <ul>
      <li><a href="#class_ba_ActivityNotFoundError">ba.ActivityNotFoundError</a></li>
      <li><a href="#class_ba_ActorNotFoundError">ba.ActorNotFoundError</a></li>
      <li><a href="#class_ba_DelegateNotFoundError">ba.DelegateNotFoundError</a></li>
      <li><a href="#class_ba_InputDeviceNotFoundError">ba.InputDeviceNotFoundError</a></li>
      <li><a href="#class_ba_NodeNotFoundError">ba.NodeNotFoundError</a></li>
      <li><a href="#class_ba_PlayerNotFoundError">ba.PlayerNotFoundError</a></li>
      <li><a href="#class_ba_SessionNotFoundError">ba.SessionNotFoundError</a></li>
      <li><a href="#class_ba_SessionPlayerNotFoundError">ba.SessionPlayerNotFoundError</a></li>
      <li><a href="#class_ba_SessionTeamNotFoundError">ba.SessionTeamNotFoundError</a></li>
      <li><a href="#class_ba_TeamNotFoundError">ba.TeamNotFoundError</a></li>
      <li><a href="#class_ba_WidgetNotFoundError">ba.WidgetNotFoundError</a></li>
   </ul>
</ul>
<h4><a name="class_category_Misc_Classes">Misc Classes</a></h4>
<ul>
   <li><a href="#class_ba_App_State">ba.App.State</a></li>
</ul>
<h4><a name="class_category_Protocols">Protocols</a></h4>
<ul>
   <li><a href="#class_ba_Existable">ba.Existable</a></li>
</ul>
<h4><a name="class_category_Settings_Classes">Settings Classes</a></h4>
<ul>
   <li><a href="#class_ba_BoolSetting">ba.BoolSetting</a></li>
   <li><a href="#class_ba_ChoiceSetting">ba.ChoiceSetting</a></li>
   <ul>
      <li><a href="#class_ba_FloatChoiceSetting">ba.FloatChoiceSetting</a></li>
      <li><a href="#class_ba_IntChoiceSetting">ba.IntChoiceSetting</a></li>
   </ul>
   <li><a href="#class_ba_FloatSetting">ba.FloatSetting</a></li>
   <li><a href="#class_ba_IntSetting">ba.IntSetting</a></li>
</ul>
<hr>
<h2><strong><a name="class_ba_Achievement">ba.Achievement</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Represents attributes and state for an individual achievement.</p>

<p>Category: <a href="#class_category_App_Classes">App Classes</a>
</p>

<h3>Attributes:</h3>
<h5><a href="#attr_ba_Achievement__complete">complete</a>, <a href="#attr_ba_Achievement__description">description</a>, <a href="#attr_ba_Achievement__description_complete">description_complete</a>, <a href="#attr_ba_Achievement__description_full">description_full</a>, <a href="#attr_ba_Achievement__description_full_complete">description_full_complete</a>, <a href="#attr_ba_Achievement__display_name">display_name</a>, <a href="#attr_ba_Achievement__hard_mode_only">hard_mode_only</a>, <a href="#attr_ba_Achievement__level_name">level_name</a>, <a href="#attr_ba_Achievement__name">name</a>, <a href="#attr_ba_Achievement__power_ranking_value">power_ranking_value</a></h5>
<dl>
<dt><h4><a name="attr_ba_Achievement__complete">complete</a></h4></dt><dd>
<p><span>bool</span></p>
<p>Whether this Achievement is currently complete.</p>

</dd>
<dt><h4><a name="attr_ba_Achievement__description">description</a></h4></dt><dd>
<p><span><a href="#class_ba_Lstr">ba.Lstr</a></span></p>
<p>Get a <a href="#class_ba_Lstr">ba.Lstr</a> for the Achievement's brief description.</p>

</dd>
<dt><h4><a name="attr_ba_Achievement__description_complete">description_complete</a></h4></dt><dd>
<p><span><a href="#class_ba_Lstr">ba.Lstr</a></span></p>
<p>Get a <a href="#class_ba_Lstr">ba.Lstr</a> for the Achievement's description when completed.</p>

</dd>
<dt><h4><a name="attr_ba_Achievement__description_full">description_full</a></h4></dt><dd>
<p><span><a href="#class_ba_Lstr">ba.Lstr</a></span></p>
<p>Get a <a href="#class_ba_Lstr">ba.Lstr</a> for the Achievement's full description.</p>

</dd>
<dt><h4><a name="attr_ba_Achievement__description_full_complete">description_full_complete</a></h4></dt><dd>
<p><span><a href="#class_ba_Lstr">ba.Lstr</a></span></p>
<p>Get a <a href="#class_ba_Lstr">ba.Lstr</a> for the Achievement's full desc. when completed.</p>

</dd>
<dt><h4><a name="attr_ba_Achievement__display_name">display_name</a></h4></dt><dd>
<p><span><a href="#class_ba_Lstr">ba.Lstr</a></span></p>
<p>Return a <a href="#class_ba_Lstr">ba.Lstr</a> for this Achievement's name.</p>

</dd>
<dt><h4><a name="attr_ba_Achievement__hard_mode_only">hard_mode_only</a></h4></dt><dd>
<p><span>bool</span></p>
<p>Whether this Achievement is only unlockable in hard-mode.</p>

</dd>
<dt><h4><a name="attr_ba_Achievement__level_name">level_name</a></h4></dt><dd>
<p><span>str</span></p>
<p>The name of the level this achievement applies to.</p>

</dd>
<dt><h4><a name="attr_ba_Achievement__name">name</a></h4></dt><dd>
<p><span>str</span></p>
<p>The name of this achievement.</p>

</dd>
<dt><h4><a name="attr_ba_Achievement__power_ranking_value">power_ranking_value</a></h4></dt><dd>
<p><span>int</span></p>
<p>Get the power-ranking award value for this achievement.</p>

</dd>
</dl>
<h3>Methods:</h3>
<h5><a href="#method_ba_Achievement____init__">&lt;constructor&gt;</a>, <a href="#method_ba_Achievement__announce_completion">announce_completion()</a>, <a href="#method_ba_Achievement__create_display">create_display()</a>, <a href="#method_ba_Achievement__get_award_ticket_value">get_award_ticket_value()</a>, <a href="#method_ba_Achievement__get_icon_color">get_icon_color()</a>, <a href="#method_ba_Achievement__get_icon_texture">get_icon_texture()</a>, <a href="#method_ba_Achievement__set_complete">set_complete()</a>, <a href="#method_ba_Achievement__show_completion_banner">show_completion_banner()</a></h5>
<dl>
<dt><h4><a name="method_ba_Achievement____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.Achievement(name: str, icon_name: str, icon_color: Sequence[float], level_name: str, award: int, hard_mode_only: bool = False)</span></p>

</dd>
<dt><h4><a name="method_ba_Achievement__announce_completion">announce_completion()</a></dt></h4><dd>
<p><span>announce_completion(self, sound: bool = True) -&gt; None</span></p>

<p>Kick off an announcement for this achievement's completion.</p>

</dd>
<dt><h4><a name="method_ba_Achievement__create_display">create_display()</a></dt></h4><dd>
<p><span>create_display(self, x: 'float', y: 'float', delay: 'float', outdelay: 'float' = None, color: 'Sequence[float]' = None, style: 'str' = 'post_game') -&gt; 'List[<a href="#class_ba_Actor">ba.Actor</a>]'</span></p>

<p>Create a display for the Achievement.</p>

<p>Shows the Achievement icon, name, and description.</p>

</dd>
<dt><h4><a name="method_ba_Achievement__get_award_ticket_value">get_award_ticket_value()</a></dt></h4><dd>
<p><span>get_award_ticket_value(self, include_pro_bonus: bool = False) -&gt; int</span></p>

<p>Get the ticket award value for this achievement.</p>

</dd>
<dt><h4><a name="method_ba_Achievement__get_icon_color">get_icon_color()</a></dt></h4><dd>
<p><span>get_icon_color(self, complete: bool) -&gt; Sequence[float]</span></p>

<p>Return the color tint for this Achievement's icon.</p>

</dd>
<dt><h4><a name="method_ba_Achievement__get_icon_texture">get_icon_texture()</a></dt></h4><dd>
<p><span>get_icon_texture(self, complete: bool) -&gt; <a href="#class_ba_Texture">ba.Texture</a></span></p>

<p>Return the icon texture to display for this achievement</p>

</dd>
<dt><h4><a name="method_ba_Achievement__set_complete">set_complete()</a></dt></h4><dd>
<p><span>set_complete(self, complete: bool = True) -&gt; None</span></p>

<p>Set an achievement's completed state.</p>

<p>note this only sets local state; use a transaction to
actually award achievements.</p>

</dd>
<dt><h4><a name="method_ba_Achievement__show_completion_banner">show_completion_banner()</a></dt></h4><dd>
<p><span>show_completion_banner(self, sound: bool = True) -&gt; None</span></p>

<p>Create the banner/sound for an acquired achievement announcement.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_AchievementSubsystem">ba.AchievementSubsystem</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Subsystem for achievement handling.</p>

<p>Category: <a href="#class_category_App_Classes">App Classes</a></p>

<p>    Access the single shared instance of this class at 'ba.app.ach'.
</p>

<h3>Methods:</h3>
<h5><a href="#method_ba_AchievementSubsystem____init__">&lt;constructor&gt;</a>, <a href="#method_ba_AchievementSubsystem__achievements_for_coop_level">achievements_for_coop_level()</a>, <a href="#method_ba_AchievementSubsystem__award_local_achievement">award_local_achievement()</a>, <a href="#method_ba_AchievementSubsystem__get_achievement">get_achievement()</a></h5>
<dl>
<dt><h4><a name="method_ba_AchievementSubsystem____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.AchievementSubsystem()</span></p>

</dd>
<dt><h4><a name="method_ba_AchievementSubsystem__achievements_for_coop_level">achievements_for_coop_level()</a></dt></h4><dd>
<p><span>achievements_for_coop_level(self, level_name: str) -&gt; List[Achievement]</span></p>

<p>Given a level name, return achievements available for it.</p>

</dd>
<dt><h4><a name="method_ba_AchievementSubsystem__award_local_achievement">award_local_achievement()</a></dt></h4><dd>
<p><span>award_local_achievement(self, achname: str) -&gt; None</span></p>

<p>For non-game-based achievements such as controller-connection.</p>

</dd>
<dt><h4><a name="method_ba_AchievementSubsystem__get_achievement">get_achievement()</a></dt></h4><dd>
<p><span>get_achievement(self, name: str) -&gt; Achievement</span></p>

<p>Return an Achievement by name.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_Activity">ba.Activity</a></strong></h3>
<p>Inherits from: <a href="#class_ba_DependencyComponent">ba.DependencyComponent</a>, <a href="https://docs.python.org/3/library/typing.html#typing.Generic">typing.Generic</a></p>
<p>Units of execution wrangled by a <a href="#class_ba_Session">ba.Session</a>.</p>

<p>Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a></p>

<p>    Examples of Activities include games, score-screens, cutscenes, etc.
    A <a href="#class_ba_Session">ba.Session</a> has one 'current' Activity at any time, though their existence
    can overlap during transitions.</p>

<h3>Attributes:</h3>
<h5><a href="#attr_ba_Activity__customdata">customdata</a>, <a href="#attr_ba_Activity__expired">expired</a>, <a href="#attr_ba_Activity__globalsnode">globalsnode</a>, <a href="#attr_ba_Activity__players">players</a>, <a href="#attr_ba_Activity__playertype">playertype</a>, <a href="#attr_ba_Activity__session">session</a>, <a href="#attr_ba_Activity__settings_raw">settings_raw</a>, <a href="#attr_ba_Activity__stats">stats</a>, <a href="#attr_ba_Activity__teams">teams</a>, <a href="#attr_ba_Activity__teamtype">teamtype</a></h5>
<dl>
<dt><h4><a name="attr_ba_Activity__customdata">customdata</a></h4></dt><dd>
<p><span>dict</span></p>
<p>Entities needing to store simple data with an activity can put it
        here. This dict will be deleted when the activity expires, so contained
        objects generally do not need to worry about handling expired
        activities.</p>

</dd>
<dt><h4><a name="attr_ba_Activity__expired">expired</a></h4></dt><dd>
<p><span>bool</span></p>
<p>Whether the activity is expired.</p>

<p>        An activity is set as expired when shutting down.
        At this point no new nodes, timers, etc should be made,
        run, etc, and the activity should be considered a 'zombie'.</p>

</dd>
<dt><h4><a name="attr_ba_Activity__globalsnode">globalsnode</a></h4></dt><dd>
<p><span><a href="#class_ba_Node">ba.Node</a></span></p>
<p>The 'globals' <a href="#class_ba_Node">ba.Node</a> for the activity. This contains various
        global controls and values.</p>

</dd>
<dt><h4><a name="attr_ba_Activity__players">players</a></h4></dt><dd>
<p><span>List[PlayerType]</span></p>
<p>The list of <a href="#class_ba_Player">ba.Players</a> in the Activity. This gets populated just
before on_begin() is called and is updated automatically as players
join or leave the game.</p>

</dd>
<dt><h4><a name="attr_ba_Activity__playertype">playertype</a></h4></dt><dd>
<p><span>Type[PlayerType]</span></p>
<p>The type of <a href="#class_ba_Player">ba.Player</a> this Activity is using.</p>

</dd>
<dt><h4><a name="attr_ba_Activity__session">session</a></h4></dt><dd>
<p><span><a href="#class_ba_Session">ba.Session</a></span></p>
<p>The <a href="#class_ba_Session">ba.Session</a> this <a href="#class_ba_Activity">ba.Activity</a> belongs go.</p>

<p>        Raises a <a href="#class_ba_SessionNotFoundError">ba.SessionNotFoundError</a> if the Session no longer exists.</p>

</dd>
<dt><h4><a name="attr_ba_Activity__settings_raw">settings_raw</a></h4></dt><dd>
<p><span>Dict[str, Any]</span></p>
<p>The settings dict passed in when the activity was made.
This attribute is deprecated and should be avoided when possible;
activities should pull all values they need from the 'settings' arg
passed to the Activity __init__ call.</p>

</dd>
<dt><h4><a name="attr_ba_Activity__stats">stats</a></h4></dt><dd>
<p><span><a href="#class_ba_Stats">ba.Stats</a></span></p>
<p>The stats instance accessible while the activity is running.</p>

<p>        If access is attempted before or after, raises a <a href="#class_ba_NotFoundError">ba.NotFoundError</a>.</p>

</dd>
<dt><h4><a name="attr_ba_Activity__teams">teams</a></h4></dt><dd>
<p><span>List[TeamType]</span></p>
<p>The list of <a href="#class_ba_Team">ba.Teams</a> in the Activity. This gets populated just before
before on_begin() is called and is updated automatically as players
join or leave the game. (at least in free-for-all mode where every
player gets their own team; in teams mode there are always 2 teams
regardless of the player count).</p>

</dd>
<dt><h4><a name="attr_ba_Activity__teamtype">teamtype</a></h4></dt><dd>
<p><span>Type[TeamType]</span></p>
<p>The type of <a href="#class_ba_Team">ba.Team</a> this Activity is using.</p>

</dd>
</dl>
<h3>Methods Inherited:</h3>
<h5><a href="#method_ba_DependencyComponent__dep_is_present">dep_is_present()</a>, <a href="#method_ba_DependencyComponent__get_dynamic_deps">get_dynamic_deps()</a></h5>
<h3>Methods Defined or Overridden:</h3>
<h5><a href="#method_ba_Activity____init__">&lt;constructor&gt;</a>, <a href="#method_ba_Activity__add_actor_weak_ref">add_actor_weak_ref()</a>, <a href="#method_ba_Activity__create_player">create_player()</a>, <a href="#method_ba_Activity__create_team">create_team()</a>, <a href="#method_ba_Activity__end">end()</a>, <a href="#method_ba_Activity__handlemessage">handlemessage()</a>, <a href="#method_ba_Activity__has_begun">has_begun()</a>, <a href="#method_ba_Activity__has_ended">has_ended()</a>, <a href="#method_ba_Activity__has_transitioned_in">has_transitioned_in()</a>, <a href="#method_ba_Activity__is_transitioning_out">is_transitioning_out()</a>, <a href="#method_ba_Activity__on_begin">on_begin()</a>, <a href="#method_ba_Activity__on_expire">on_expire()</a>, <a href="#method_ba_Activity__on_player_join">on_player_join()</a>, <a href="#method_ba_Activity__on_player_leave">on_player_leave()</a>, <a href="#method_ba_Activity__on_team_join">on_team_join()</a>, <a href="#method_ba_Activity__on_team_leave">on_team_leave()</a>, <a href="#method_ba_Activity__on_transition_in">on_transition_in()</a>, <a href="#method_ba_Activity__on_transition_out">on_transition_out()</a>, <a href="#method_ba_Activity__retain_actor">retain_actor()</a>, <a href="#method_ba_Activity__transition_out">transition_out()</a></h5>
<dl>
<dt><h4><a name="method_ba_Activity____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.Activity(settings: dict)</span></p>

<p>Creates an Activity in the current <a href="#class_ba_Session">ba.Session</a>.</p>

<p>The activity will not be actually run until <a href="#method_ba_Session__setactivity">ba.Session.setactivity</a>()
is called. 'settings' should be a dict of key/value pairs specific
to the activity.</p>

<p>Activities should preload as much of their media/etc as possible in
their constructor, but none of it should actually be used until they
are transitioned in.</p>

</dd>
<dt><h4><a name="method_ba_Activity__add_actor_weak_ref">add_actor_weak_ref()</a></dt></h4><dd>
<p><span>add_actor_weak_ref(self, actor: <a href="#class_ba_Actor">ba.Actor</a>) -&gt; None</span></p>

<p>Add a weak-reference to a <a href="#class_ba_Actor">ba.Actor</a> to the <a href="#class_ba_Activity">ba.Activity</a>.</p>

<p>(called by the <a href="#class_ba_Actor">ba.Actor</a> base class)</p>

</dd>
<dt><h4><a name="method_ba_Activity__create_player">create_player()</a></dt></h4><dd>
<p><span>create_player(self, sessionplayer: <a href="#class_ba_SessionPlayer">ba.SessionPlayer</a>) -&gt; PlayerType</span></p>

<p>Create the Player instance for this Activity.</p>

<p>Subclasses can override this if the activity's player class
requires a custom constructor; otherwise it will be called with
no args. Note that the player object should not be used at this
point as it is not yet fully wired up; wait for on_player_join()
for that.</p>

</dd>
<dt><h4><a name="method_ba_Activity__create_team">create_team()</a></dt></h4><dd>
<p><span>create_team(self, sessionteam: <a href="#class_ba_SessionTeam">ba.SessionTeam</a>) -&gt; TeamType</span></p>

<p>Create the Team instance for this Activity.</p>

<p>Subclasses can override this if the activity's team class
requires a custom constructor; otherwise it will be called with
no args. Note that the team object should not be used at this
point as it is not yet fully wired up; wait for on_team_join()
for that.</p>

</dd>
<dt><h4><a name="method_ba_Activity__end">end()</a></dt></h4><dd>
<p><span>end(self, results: Any = None, delay: float = 0.0, force: bool = False) -&gt; None</span></p>

<p>Commences Activity shutdown and delivers results to the <a href="#class_ba_Session">ba.Session</a>.</p>

<p>'delay' is the time delay before the Activity actually ends
(in seconds). Further calls to end() will be ignored up until
this time, unless 'force' is True, in which case the new results
will replace the old.</p>

</dd>
<dt><h4><a name="method_ba_Activity__handlemessage">handlemessage()</a></dt></h4><dd>
<p><span>handlemessage(self, msg: Any) -&gt; Any</span></p>

<p>General message handling; can be passed any <a href="#class_category_Message_Classes">message object</a>.</p>

</dd>
<dt><h4><a name="method_ba_Activity__has_begun">has_begun()</a></dt></h4><dd>
<p><span>has_begun(self) -&gt; bool</span></p>

<p>Return whether on_begin() has been called.</p>

</dd>
<dt><h4><a name="method_ba_Activity__has_ended">has_ended()</a></dt></h4><dd>
<p><span>has_ended(self) -&gt; bool</span></p>

<p>Return whether the activity has commenced ending.</p>

</dd>
<dt><h4><a name="method_ba_Activity__has_transitioned_in">has_transitioned_in()</a></dt></h4><dd>
<p><span>has_transitioned_in(self) -&gt; bool</span></p>

<p>Return whether on_transition_in() has been called.</p>

</dd>
<dt><h4><a name="method_ba_Activity__is_transitioning_out">is_transitioning_out()</a></dt></h4><dd>
<p><span>is_transitioning_out(self) -&gt; bool</span></p>

<p>Return whether on_transition_out() has been called.</p>

</dd>
<dt><h4><a name="method_ba_Activity__on_begin">on_begin()</a></dt></h4><dd>
<p><span>on_begin(self) -&gt; None</span></p>

<p>Called once the previous <a href="#class_ba_Activity">ba.Activity</a> has finished transitioning out.</p>

<p>At this point the activity's initial players and teams are filled in
and it should begin its actual game logic.</p>

</dd>
<dt><h4><a name="method_ba_Activity__on_expire">on_expire()</a></dt></h4><dd>
<p><span>on_expire(self) -&gt; None</span></p>

<p>Called when your activity is being expired.</p>

<p>If your activity has created anything explicitly that may be retaining
a strong reference to the activity and preventing it from dying, you
should clear that out here. From this point on your activity's sole
purpose in life is to hit zero references and die so the next activity
can begin.</p>

</dd>
<dt><h4><a name="method_ba_Activity__on_player_join">on_player_join()</a></dt></h4><dd>
<p><span>on_player_join(self, player: PlayerType) -&gt; None</span></p>

<p>Called when a new <a href="#class_ba_Player">ba.Player</a> has joined the Activity.</p>

<p>(including the initial set of Players)</p>

</dd>
<dt><h4><a name="method_ba_Activity__on_player_leave">on_player_leave()</a></dt></h4><dd>
<p><span>on_player_leave(self, player: PlayerType) -&gt; None</span></p>

<p>Called when a <a href="#class_ba_Player">ba.Player</a> is leaving the Activity.</p>

</dd>
<dt><h4><a name="method_ba_Activity__on_team_join">on_team_join()</a></dt></h4><dd>
<p><span>on_team_join(self, team: TeamType) -&gt; None</span></p>

<p>Called when a new <a href="#class_ba_Team">ba.Team</a> joins the Activity.</p>

<p>(including the initial set of Teams)</p>

</dd>
<dt><h4><a name="method_ba_Activity__on_team_leave">on_team_leave()</a></dt></h4><dd>
<p><span>on_team_leave(self, team: TeamType) -&gt; None</span></p>

<p>Called when a <a href="#class_ba_Team">ba.Team</a> leaves the Activity.</p>

</dd>
<dt><h4><a name="method_ba_Activity__on_transition_in">on_transition_in()</a></dt></h4><dd>
<p><span>on_transition_in(self) -&gt; None</span></p>

<p>Called when the Activity is first becoming visible.</p>

<p>Upon this call, the Activity should fade in backgrounds,
start playing music, etc. It does not yet have access to players
or teams, however. They remain owned by the previous Activity
up until <a href="#method_ba_Activity__on_begin">ba.Activity.on_begin</a>() is called.</p>

</dd>
<dt><h4><a name="method_ba_Activity__on_transition_out">on_transition_out()</a></dt></h4><dd>
<p><span>on_transition_out(self) -&gt; None</span></p>

<p>Called when your activity begins transitioning out.</p>

<p>Note that this may happen at any time even if end() has not been
called.</p>

</dd>
<dt><h4><a name="method_ba_Activity__retain_actor">retain_actor()</a></dt></h4><dd>
<p><span>retain_actor(self, actor: <a href="#class_ba_Actor">ba.Actor</a>) -&gt; None</span></p>

<p>Add a strong-reference to a <a href="#class_ba_Actor">ba.Actor</a> to this Activity.</p>

<p>The reference will be lazily released once <a href="#method_ba_Actor__exists">ba.Actor.exists</a>()
returns False for the Actor. The <a href="#method_ba_Actor__autoretain">ba.Actor.autoretain</a>() method
is a convenient way to access this same functionality.</p>

</dd>
<dt><h4><a name="method_ba_Activity__transition_out">transition_out()</a></dt></h4><dd>
<p><span>transition_out(self) -&gt; None</span></p>

<p>Called by the Session to start us transitioning out.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_ActivityNotFoundError">ba.ActivityNotFoundError</a></strong></h3>
<p>Inherits from: <a href="#class_ba_NotFoundError">ba.NotFoundError</a>, <a href="https://docs.python.org/3/library/exceptions.html#Exception">Exception</a>, <a href="https://docs.python.org/3/library/exceptions.html#BaseException">BaseException</a></p>
<p>Exception raised when an expected <a href="#class_ba_Activity">ba.Activity</a> does not exist.</p>

<p>Category: <a href="#class_category_Exception_Classes">Exception Classes</a>
</p>

<h3>Methods:</h3>
<p>&lt;all methods inherited from <a href="#class_ba_NotFoundError">ba.NotFoundError</a>&gt;</p>
<hr>
<h2><strong><a name="class_ba_Actor">ba.Actor</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>High level logical entities in a <a href="#class_ba_Activity">ba.Activity</a>.</p>

<p>Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a></p>

<p>    Actors act as controllers, combining some number of <a href="#class_ba_Node">ba.Nodes</a>,
    <a href="#class_ba_Texture">ba.Textures</a>, <a href="#class_ba_Sound">ba.Sounds</a>, etc. into a high-level cohesive unit.</p>

<p>    Some example actors include the Bomb, Flag, and Spaz classes that
    live in the bastd.actor.* modules.</p>

<p>    One key feature of Actors is that they generally 'die'
    (killing off or transitioning out their nodes) when the last Python
    reference to them disappears, so you can use logic such as:</p>

<pre><span><em><small>    # Create a flag Actor in our game activity:</small></em></span>
    from bastd.actor.flag import Flag
    self.flag = Flag(position=(0, 10, 0))</pre>

<pre><span><em><small>    # Later, destroy the flag.</small></em></span>
<span><em><small>    # (provided nothing else is holding a reference to it)</small></em></span>
<span><em><small>    # We could also just assign a new flag to this value.</small></em></span>
<span><em><small>    # Either way, the old flag disappears.</small></em></span>
    self.flag = None</pre>

<p>    This is in contrast to the behavior of the more low level <a href="#class_ba_Node">ba.Nodes</a>,
    which are always explicitly created and destroyed and don't care
    how many Python references to them exist.</p>

<p>    Note, however, that you can use the <a href="#method_ba_Actor__autoretain">ba.Actor.autoretain</a>() method
    if you want an Actor to stick around until explicitly killed
    regardless of references.</p>

<p>    Another key feature of <a href="#class_ba_Actor">ba.Actor</a> is its handlemessage() method, which
    takes a single arbitrary object as an argument. This provides a safe way
    to communicate between <a href="#class_ba_Actor">ba.Actor</a>, <a href="#class_ba_Activity">ba.Activity</a>, <a href="#class_ba_Session">ba.Session</a>, and any other
    class providing a handlemessage() method.  The most universally handled
    message type for Actors is the <a href="#class_ba_DieMessage">ba.DieMessage</a>.</p>

<pre><span><em><small>    # Another way to kill the flag from the example above:</small></em></span>
<span><em><small>    # We can safely call this on any type with a 'handlemessage' method</small></em></span>
<span><em><small>    # (though its not guaranteed to always have a meaningful effect).</small></em></span>
<span><em><small>    # In this case the Actor instance will still be around, but its exists()</small></em></span>
<span><em><small>    # and is_alive() methods will both return False.</small></em></span>
    self.flag.handlemessage(<a href="#class_ba_DieMessage">ba.DieMessage</a>())
</pre>

<h3>Attributes:</h3>
<h5><a href="#attr_ba_Actor__activity">activity</a>, <a href="#attr_ba_Actor__expired">expired</a></h5>
<dl>
<dt><h4><a name="attr_ba_Actor__activity">activity</a></h4></dt><dd>
<p><span><a href="#class_ba_Activity">ba.Activity</a></span></p>
<p>The Activity this Actor was created in.</p>

<p>        Raises a <a href="#class_ba_ActivityNotFoundError">ba.ActivityNotFoundError</a> if the Activity no longer exists.</p>

</dd>
<dt><h4><a name="attr_ba_Actor__expired">expired</a></h4></dt><dd>
<p><span>bool</span></p>
<p>Whether the Actor is expired.</p>

<p>        (see <a href="#method_ba_Actor__on_expire">ba.Actor.on_expire</a>())</p>

</dd>
</dl>
<h3>Methods:</h3>
<h5><a href="#method_ba_Actor____init__">&lt;constructor&gt;</a>, <a href="#method_ba_Actor__autoretain">autoretain()</a>, <a href="#method_ba_Actor__exists">exists()</a>, <a href="#method_ba_Actor__getactivity">getactivity()</a>, <a href="#method_ba_Actor__handlemessage">handlemessage()</a>, <a href="#method_ba_Actor__is_alive">is_alive()</a>, <a href="#method_ba_Actor__on_expire">on_expire()</a></h5>
<dl>
<dt><h4><a name="method_ba_Actor____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.Actor()</span></p>

<p>Instantiates an Actor in the current <a href="#class_ba_Activity">ba.Activity</a>.</p>

</dd>
<dt><h4><a name="method_ba_Actor__autoretain">autoretain()</a></dt></h4><dd>
<p><span>autoretain(self: T) -&gt; T</span></p>

<p>Keep this Actor alive without needing to hold a reference to it.</p>

<p>This keeps the <a href="#class_ba_Actor">ba.Actor</a> in existence by storing a reference to it
with the <a href="#class_ba_Activity">ba.Activity</a> it was created in. The reference is lazily
released once <a href="#method_ba_Actor__exists">ba.Actor.exists</a>() returns False for it or when the
Activity is set as expired.  This can be a convenient alternative
to storing references explicitly just to keep a <a href="#class_ba_Actor">ba.Actor</a> from dying.
For convenience, this method returns the <a href="#class_ba_Actor">ba.Actor</a> it is called with,
enabling chained statements such as:  myflag = ba.Flag().autoretain()</p>

</dd>
<dt><h4><a name="method_ba_Actor__exists">exists()</a></dt></h4><dd>
<p><span>exists(self) -&gt; bool</span></p>

<p>Returns whether the Actor is still present in a meaningful way.</p>

<p>Note that a dying character should still return True here as long as
their corpse is visible; this is about presence, not being 'alive'
(see <a href="#method_ba_Actor__is_alive">ba.Actor.is_alive</a>() for that).</p>

<p>If this returns False, it is assumed the Actor can be completely
deleted without affecting the game; this call is often used
when pruning lists of Actors, such as with <a href="#method_ba_Actor__autoretain">ba.Actor.autoretain</a>()</p>

<p>The default implementation of this method always return True.</p>

<p>Note that the boolean operator for the Actor class calls this method,
so a simple "if myactor" test will conveniently do the right thing
even if myactor is set to None.</p>

</dd>
<dt><h4><a name="method_ba_Actor__getactivity">getactivity()</a></dt></h4><dd>
<p><span>getactivity(self, doraise: bool = True) -&gt; Optional[<a href="#class_ba_Activity">ba.Activity</a>]</span></p>

<p>Return the <a href="#class_ba_Activity">ba.Activity</a> this Actor is associated with.</p>

<p>If the Activity no longer exists, raises a <a href="#class_ba_ActivityNotFoundError">ba.ActivityNotFoundError</a>
or returns None depending on whether 'doraise' is True.</p>

</dd>
<dt><h4><a name="method_ba_Actor__handlemessage">handlemessage()</a></dt></h4><dd>
<p><span>handlemessage(self, msg: Any) -&gt; Any</span></p>

<p>General message handling; can be passed any <a href="#class_category_Message_Classes">message object</a>.</p>

</dd>
<dt><h4><a name="method_ba_Actor__is_alive">is_alive()</a></dt></h4><dd>
<p><span>is_alive(self) -&gt; bool</span></p>

<p>Returns whether the Actor is 'alive'.</p>

<p>What this means is up to the Actor.
It is not a requirement for Actors to be able to die;
just that they report whether they consider themselves
to be alive or not. In cases where dead/alive is
irrelevant, True should be returned.</p>

</dd>
<dt><h4><a name="method_ba_Actor__on_expire">on_expire()</a></dt></h4><dd>
<p><span>on_expire(self) -&gt; None</span></p>

<p>Called for remaining <a href="#class_ba_Actor">ba.Actors</a> when their <a href="#class_ba_Activity">ba.Activity</a> shuts down.</p>

<p>Actors can use this opportunity to clear callbacks or other
references which have the potential of keeping the <a href="#class_ba_Activity">ba.Activity</a>
alive inadvertently (Activities can not exit cleanly while
any Python references to them remain.)</p>

<p>Once an actor is expired (see <a href="#class_ba_Actor">ba.Actor</a>.is_expired()) it should no
longer perform any game-affecting operations (creating, modifying,
or deleting nodes, media, timers, etc.) Attempts to do so will
likely result in errors.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_ActorNotFoundError">ba.ActorNotFoundError</a></strong></h3>
<p>Inherits from: <a href="#class_ba_NotFoundError">ba.NotFoundError</a>, <a href="https://docs.python.org/3/library/exceptions.html#Exception">Exception</a>, <a href="https://docs.python.org/3/library/exceptions.html#BaseException">BaseException</a></p>
<p>Exception raised when an expected <a href="#class_ba_Actor">ba.Actor</a> does not exist.</p>

<p>Category: <a href="#class_category_Exception_Classes">Exception Classes</a>
</p>

<h3>Methods:</h3>
<p>&lt;all methods inherited from <a href="#class_ba_NotFoundError">ba.NotFoundError</a>&gt;</p>
<hr>
<h2><strong><a name="class_ba_App">ba.App</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>A class for high level app functionality and state.</p>

<p>Category: <a href="#class_category_App_Classes">App Classes</a></p>

<p>    Use ba.app to access the single shared instance of this class.</p>

<p>    Note that properties not documented here should be considered internal
    and subject to change without warning.
</p>

<h3>Attributes:</h3>
<h5><a href="#attr_ba_App__api_version">api_version</a>, <a href="#attr_ba_App__build_number">build_number</a>, <a href="#attr_ba_App__config">config</a>, <a href="#attr_ba_App__config_file_path">config_file_path</a>, <a href="#attr_ba_App__debug_build">debug_build</a>, <a href="#attr_ba_App__on_tv">on_tv</a>, <a href="#attr_ba_App__platform">platform</a>, <a href="#attr_ba_App__python_directory_app">python_directory_app</a>, <a href="#attr_ba_App__python_directory_app_site">python_directory_app_site</a>, <a href="#attr_ba_App__python_directory_user">python_directory_user</a>, <a href="#attr_ba_App__subplatform">subplatform</a>, <a href="#attr_ba_App__test_build">test_build</a>, <a href="#attr_ba_App__ui_bounds">ui_bounds</a>, <a href="#attr_ba_App__user_agent_string">user_agent_string</a>, <a href="#attr_ba_App__version">version</a>, <a href="#attr_ba_App__vr_mode">vr_mode</a></h5>
<dl>
<dt><h4><a name="attr_ba_App__api_version">api_version</a></h4></dt><dd>
<p><span>int</span></p>
<p>The game's api version.</p>

<p>        Only Python modules and packages associated with the current API
        version number will be detected by the game (see the ba_meta tag).
        This value will change whenever backward-incompatible changes are
        introduced to game APIs. When that happens, scripts should be updated
        accordingly and set to target the new API version number.</p>

</dd>
<dt><h4><a name="attr_ba_App__build_number">build_number</a></h4></dt><dd>
<p><span>int</span></p>
<p>Integer build number.</p>

<p>        This value increases by at least 1 with each release of the game.
        It is independent of the human readable <a href="#attr_ba_App__version">ba.App.version</a> string.</p>

</dd>
<dt><h4><a name="attr_ba_App__config">config</a></h4></dt><dd>
<p><span><a href="#class_ba_AppConfig">ba.AppConfig</a></span></p>
<p>The <a href="#class_ba_AppConfig">ba.AppConfig</a> instance representing the app's config state.</p>

</dd>
<dt><h4><a name="attr_ba_App__config_file_path">config_file_path</a></h4></dt><dd>
<p><span>str</span></p>
<p>Where the game's config file is stored on disk.</p>

</dd>
<dt><h4><a name="attr_ba_App__debug_build">debug_build</a></h4></dt><dd>
<p><span>bool</span></p>
<p>Whether the game was compiled in debug mode.</p>

<p>        Debug builds generally run substantially slower than non-debug
        builds due to compiler optimizations being disabled and extra
        checks being run.</p>

</dd>
<dt><h4><a name="attr_ba_App__on_tv">on_tv</a></h4></dt><dd>
<p><span>bool</span></p>
<p>Whether the game is currently running on a TV.</p>

</dd>
<dt><h4><a name="attr_ba_App__platform">platform</a></h4></dt><dd>
<p><span>str</span></p>
<p>Name of the current platform.</p>

<p>        Examples are: 'mac', 'windows', android'.</p>

</dd>
<dt><h4><a name="attr_ba_App__python_directory_app">python_directory_app</a></h4></dt><dd>
<p><span>str</span></p>
<p>Path where the app looks for its bundled scripts.</p>

</dd>
<dt><h4><a name="attr_ba_App__python_directory_app_site">python_directory_app_site</a></h4></dt><dd>
<p><span>str</span></p>
<p>Path containing pip packages bundled with the app.</p>

</dd>
<dt><h4><a name="attr_ba_App__python_directory_user">python_directory_user</a></h4></dt><dd>
<p><span>str</span></p>
<p>Path where the app looks for custom user scripts.</p>

</dd>
<dt><h4><a name="attr_ba_App__subplatform">subplatform</a></h4></dt><dd>
<p><span>str</span></p>
<p>String for subplatform.</p>

<p>        Can be empty. For the 'android' platform, subplatform may
        be 'google', 'amazon', etc.</p>

</dd>
<dt><h4><a name="attr_ba_App__test_build">test_build</a></h4></dt><dd>
<p><span>bool</span></p>
<p>Whether the game was compiled in test mode.</p>

<p>        Test mode enables extra checks and features that are useful for
        release testing but which do not slow the game down significantly.</p>

</dd>
<dt><h4><a name="attr_ba_App__ui_bounds">ui_bounds</a></h4></dt><dd>
<p><span>Tuple[float, float, float, float]</span></p>
<p>Bounds of the 'safe' screen area in ui space.</p>

<p>        This tuple contains: (x-min, x-max, y-min, y-max)</p>

</dd>
<dt><h4><a name="attr_ba_App__user_agent_string">user_agent_string</a></h4></dt><dd>
<p><span>str</span></p>
<p>String containing various bits of info about OS/device/etc.</p>

</dd>
<dt><h4><a name="attr_ba_App__version">version</a></h4></dt><dd>
<p><span>str</span></p>
<p>Human-readable version string; something like '1.3.24'.</p>

<p>        This should not be interpreted as a number; it may contain
        string elements such as 'alpha', 'beta', 'test', etc.
        If a numeric version is needed, use '<a href="#attr_ba_App__build_number">ba.App.build_number</a>'.</p>

</dd>
<dt><h4><a name="attr_ba_App__vr_mode">vr_mode</a></h4></dt><dd>
<p><span>bool</span></p>
<p>Whether the game is currently running in VR.</p>

</dd>
</dl>
<h3>Methods:</h3>
<h5><a href="#method_ba_App__handle_deep_link">handle_deep_link()</a>, <a href="#method_ba_App__launch_coop_game">launch_coop_game()</a>, <a href="#method_ba_App__on_app_pause">on_app_pause()</a>, <a href="#method_ba_App__on_app_resume">on_app_resume()</a>, <a href="#method_ba_App__pause">pause()</a>, <a href="#method_ba_App__resume">resume()</a>, <a href="#method_ba_App__return_to_main_menu_session_gracefully">return_to_main_menu_session_gracefully()</a></h5>
<dl>
<dt><h4><a name="method_ba_App__handle_deep_link">handle_deep_link()</a></dt></h4><dd>
<p><span>handle_deep_link(self, url: str) -&gt; None</span></p>

<p>Handle a deep link URL.</p>

</dd>
<dt><h4><a name="method_ba_App__launch_coop_game">launch_coop_game()</a></dt></h4><dd>
<p><span>launch_coop_game(self, game: str, force: bool = False, args: Dict = None) -&gt; bool</span></p>

<p>High level way to launch a local co-op session.</p>

</dd>
<dt><h4><a name="method_ba_App__on_app_pause">on_app_pause()</a></dt></h4><dd>
<p><span>on_app_pause(self) -&gt; None</span></p>

<p>Called when the app goes to a suspended state.</p>

</dd>
<dt><h4><a name="method_ba_App__on_app_resume">on_app_resume()</a></dt></h4><dd>
<p><span>on_app_resume(self) -&gt; None</span></p>

<p>Run when the app resumes from a suspended state.</p>

</dd>
<dt><h4><a name="method_ba_App__pause">pause()</a></dt></h4><dd>
<p><span>pause(self) -&gt; None</span></p>

<p>Pause the game due to a user request or menu popping up.</p>

<p>If there's a foreground host-activity that says it's pausable, tell it
to pause ..we now no longer pause if there are connected clients.</p>

</dd>
<dt><h4><a name="method_ba_App__resume">resume()</a></dt></h4><dd>
<p><span>resume(self) -&gt; None</span></p>

<p>Resume the game due to a user request or menu closing.</p>

<p>If there's a foreground host-activity that's currently paused, tell it
to resume.</p>

</dd>
<dt><h4><a name="method_ba_App__return_to_main_menu_session_gracefully">return_to_main_menu_session_gracefully()</a></dt></h4><dd>
<p><span>return_to_main_menu_session_gracefully(self, reset_ui: bool = True) -&gt; None</span></p>

<p>Attempt to cleanly get back to the main menu.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_App_State">ba.App.State</a></strong></h3>
<p>Inherits from: <a href="https://docs.python.org/3/library/enum.html#enum.Enum">enum.Enum</a></p>
<p>High level state the app can be in.</p>

<h3>Values:</h3>
<ul>
<li>LAUNCHING</li>
<li>RUNNING</li>
<li>PAUSED</li>
<li>SHUTTING_DOWN</li>
</ul>
<hr>
<h2><strong><a name="class_ba_AppConfig">ba.AppConfig</a></strong></h3>
<p>Inherits from: builtins.dict</p>
<p>A special dict that holds the game's persistent configuration values.</p>

<p>Category: <a href="#class_category_App_Classes">App Classes</a></p>

<p>    It also provides methods for fetching values with app-defined fallback
    defaults, applying contained values to the game, and committing the
    config to storage.</p>

<p>    Call ba.appconfig() to get the single shared instance of this class.</p>

<p>    AppConfig data is stored as json on disk on so make sure to only place
    json-friendly values in it (dict, list, str, float, int, bool).
    Be aware that tuples will be quietly converted to lists when stored.
</p>

<h3>Methods Defined or Overridden:</h3>
<h5><a href="#method_ba_AppConfig__apply">apply()</a>, <a href="#method_ba_AppConfig__apply_and_commit">apply_and_commit()</a>, <a href="#method_ba_AppConfig__builtin_keys">builtin_keys()</a>, <a href="#method_ba_AppConfig__commit">commit()</a>, <a href="#method_ba_AppConfig__default_value">default_value()</a>, <a href="#method_ba_AppConfig__resolve">resolve()</a></h5>
<dl>
<dt><h4><a name="method_ba_AppConfig__apply">apply()</a></dt></h4><dd>
<p><span>apply(self) -&gt; None</span></p>

<p>Apply config values to the running app.</p>

</dd>
<dt><h4><a name="method_ba_AppConfig__apply_and_commit">apply_and_commit()</a></dt></h4><dd>
<p><span>apply_and_commit(self) -&gt; None</span></p>

<p>Run apply() followed by commit(); for convenience.</p>

<p>(This way the commit() will not occur if apply() hits invalid data)</p>

</dd>
<dt><h4><a name="method_ba_AppConfig__builtin_keys">builtin_keys()</a></dt></h4><dd>
<p><span>builtin_keys(self) -&gt; List[str]</span></p>

<p>Return the list of valid key names recognized by <a href="#class_ba_AppConfig">ba.AppConfig</a>.</p>

<p>This set of keys can be used with resolve(), default_value(), etc.
It does not vary across platforms and may include keys that are
obsolete or not relevant on the current running version. (for instance,
VR related keys on non-VR platforms). This is to minimize the amount
of platform checking necessary)</p>

<p>Note that it is perfectly legal to store arbitrary named data in the
config, but in that case it is up to the user to test for the existence
of the key in the config dict, fall back to consistent defaults, etc.</p>

</dd>
<dt><h4><a name="method_ba_AppConfig__commit">commit()</a></dt></h4><dd>
<p><span>commit(self) -&gt; None</span></p>

<p>Commits the config to local storage.</p>

<p>Note that this call is asynchronous so the actual write to disk may not
occur immediately.</p>

</dd>
<dt><h4><a name="method_ba_AppConfig__default_value">default_value()</a></dt></h4><dd>
<p><span>default_value(self, key: str) -&gt; Any</span></p>

<p>Given a string key, return its predefined default value.</p>

<p>This is the value that will be returned by <a href="#method_ba_AppConfig__resolve">ba.AppConfig.resolve</a>() if
the key is not present in the config dict or of an incompatible type.</p>

<p>Raises an Exception for unrecognized key names. To get the list of keys
supported by this method, use <a href="#method_ba_AppConfig__builtin_keys">ba.AppConfig.builtin_keys</a>(). Note that it
is perfectly legal to store other data in the config; it just needs to
be accessed through standard dict methods and missing values handled
manually.</p>

</dd>
<dt><h4><a name="method_ba_AppConfig__resolve">resolve()</a></dt></h4><dd>
<p><span>resolve(self, key: str) -&gt; Any</span></p>

<p>Given a string key, return a config value (type varies).</p>

<p>This will substitute application defaults for values not present in
the config dict, filter some invalid values, etc.  Note that these
values do not represent the state of the app; simply the state of its
config. Use <a href="#class_ba_App">ba.App</a> to access actual live state.</p>

<p>Raises an Exception for unrecognized key names. To get the list of keys
supported by this method, use <a href="#method_ba_AppConfig__builtin_keys">ba.AppConfig.builtin_keys</a>(). Note that it
is perfectly legal to store other data in the config; it just needs to
be accessed through standard dict methods and missing values handled
manually.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_AppDelegate">ba.AppDelegate</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Defines handlers for high level app functionality.</p>

<p>Category: <a href="#class_category_App_Classes">App Classes</a>
</p>

<h3>Methods:</h3>
<dl>
<dt><h4><a name="method_ba_AppDelegate__create_default_game_settings_ui">create_default_game_settings_ui()</a></dt></h4><dd>
<p><span>create_default_game_settings_ui(self, gameclass: Type[<a href="#class_ba_GameActivity">ba.GameActivity</a>], sessiontype: Type[<a href="#class_ba_Session">ba.Session</a>], settings: Optional[dict], completion_call: Callable[[Optional[dict]], None]) -&gt; None</span></p>

<p>Launch a UI to configure the given game config.</p>

<p>It should manipulate the contents of config and call completion_call
when done.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_AssetPackage">ba.AssetPackage</a></strong></h3>
<p>Inherits from: <a href="#class_ba_DependencyComponent">ba.DependencyComponent</a></p>
<p><a href="#class_ba_DependencyComponent">ba.DependencyComponent</a> representing a bundled package of game assets.</p>

<p>Category: <a href="#class_category_Asset_Classes">Asset Classes</a>
</p>

<h3>Methods Inherited:</h3>
<h5><a href="#method_ba_DependencyComponent__get_dynamic_deps">get_dynamic_deps()</a></h5>
<h3>Methods Defined or Overridden:</h3>
<h5><a href="#method_ba_AssetPackage____init__">&lt;constructor&gt;</a>, <a href="#method_ba_AssetPackage__dep_is_present">dep_is_present()</a>, <a href="#method_ba_AssetPackage__getcollidemodel">getcollidemodel()</a>, <a href="#method_ba_AssetPackage__getdata">getdata()</a>, <a href="#method_ba_AssetPackage__getmodel">getmodel()</a>, <a href="#method_ba_AssetPackage__getsound">getsound()</a>, <a href="#method_ba_AssetPackage__gettexture">gettexture()</a></h5>
<dl>
<dt><h4><a name="method_ba_AssetPackage____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.AssetPackage()</span></p>

<p>Instantiate a DependencyComponent.</p>

</dd>
<dt><h4><a name="method_ba_AssetPackage__dep_is_present">dep_is_present()</a></dt></h4><dd>
<h5><span><em>&lt;class method&gt;</span></em></h5>
<p><span>dep_is_present(config: Any = None) -&gt; bool </span></p>

<p>Return whether this component/config is present on this device.</p>

</dd>
<dt><h4><a name="method_ba_AssetPackage__getcollidemodel">getcollidemodel()</a></dt></h4><dd>
<p><span>getcollidemodel(self, name: str) -&gt; <a href="#class_ba_CollideModel">ba.CollideModel</a></span></p>

<p>Load a named <a href="#class_ba_CollideModel">ba.CollideModel</a> from the AssetPackage.</p>

<p>Behavior is similar to ba.getcollideModel()</p>

</dd>
<dt><h4><a name="method_ba_AssetPackage__getdata">getdata()</a></dt></h4><dd>
<p><span>getdata(self, name: str) -&gt; <a href="#class_ba_Data">ba.Data</a></span></p>

<p>Load a named <a href="#class_ba_Data">ba.Data</a> from the AssetPackage.</p>

<p>Behavior is similar to ba.getdata()</p>

</dd>
<dt><h4><a name="method_ba_AssetPackage__getmodel">getmodel()</a></dt></h4><dd>
<p><span>getmodel(self, name: str) -&gt; <a href="#class_ba_Model">ba.Model</a></span></p>

<p>Load a named <a href="#class_ba_Model">ba.Model</a> from the AssetPackage.</p>

<p>Behavior is similar to <a href="#function_ba_getmodel">ba.getmodel</a>()</p>

</dd>
<dt><h4><a name="method_ba_AssetPackage__getsound">getsound()</a></dt></h4><dd>
<p><span>getsound(self, name: str) -&gt; <a href="#class_ba_Sound">ba.Sound</a></span></p>

<p>Load a named <a href="#class_ba_Sound">ba.Sound</a> from the AssetPackage.</p>

<p>Behavior is similar to <a href="#function_ba_getsound">ba.getsound</a>()</p>

</dd>
<dt><h4><a name="method_ba_AssetPackage__gettexture">gettexture()</a></dt></h4><dd>
<p><span>gettexture(self, name: str) -&gt; <a href="#class_ba_Texture">ba.Texture</a></span></p>

<p>Load a named <a href="#class_ba_Texture">ba.Texture</a> from the AssetPackage.</p>

<p>Behavior is similar to <a href="#function_ba_gettexture">ba.gettexture</a>()</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_BoolSetting">ba.BoolSetting</a></strong></h3>
<p>Inherits from: <a href="#class_ba_Setting">ba.Setting</a></p>
<p>A boolean game setting.</p>

<p>Category: <a href="#class_category_Settings_Classes">Settings Classes</a>
</p>

<h3>Methods:</h3>
<dl>
<dt><h4><a name="method_ba_BoolSetting____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.BoolSetting(name: str, default: bool)</span></p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_Call">ba.Call</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Wraps a callable and arguments into a single callable object.</p>

<p>Category: <a href="#class_category_General_Utility_Classes">General Utility Classes</a></p>

<p>    The callable is strong-referenced so it won't die until this
    object does.</p>

<p>    Note that a bound method (ex: myobj.dosomething) contains a reference
    to 'self' (myobj in that case), so you will be keeping that object
    alive too. Use <a href="#class_ba_WeakCall">ba.WeakCall</a> if you want to pass a method to callback
    without keeping its object alive.
</p>

<h3>Methods:</h3>
<dl>
<dt><h4><a name="method_ba_Call____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.Call(*args: Any, **keywds: Any)</span></p>

<p>Instantiate a Call.</p>

<p>Pass a callable as the first arg, followed by any number of
arguments or keywords.</p>

<pre><span><em><small># Example: wrap a method call with 1 positional and 1 keyword arg:</small></em></span>
mycall = ba.Call(myobj.dostuff, argval1, namedarg=argval2)</pre>

<pre><span><em><small># Now we have a single callable to run that whole mess.</small></em></span>
<span><em><small># ..the same as calling myobj.dostuff(argval1, namedarg=argval2)</small></em></span>
mycall()</pre>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_Campaign">ba.Campaign</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Represents a unique set or series of <a href="#class_ba_Level">ba.Levels</a>.</p>

<p>Category: <a href="#class_category_App_Classes">App Classes</a>
</p>

<h3>Attributes:</h3>
<h5><a href="#attr_ba_Campaign__configdict">configdict</a>, <a href="#attr_ba_Campaign__levels">levels</a>, <a href="#attr_ba_Campaign__name">name</a>, <a href="#attr_ba_Campaign__sequential">sequential</a></h5>
<dl>
<dt><h4><a name="attr_ba_Campaign__configdict">configdict</a></h4></dt><dd>
<p><span>Dict[str, Any]</span></p>
<p>Return the live config dict for this campaign.</p>

</dd>
<dt><h4><a name="attr_ba_Campaign__levels">levels</a></h4></dt><dd>
<p><span>List[<a href="#class_ba_Level">ba.Level</a>]</span></p>
<p>The list of <a href="#class_ba_Level">ba.Levels</a> in the Campaign.</p>

</dd>
<dt><h4><a name="attr_ba_Campaign__name">name</a></h4></dt><dd>
<p><span>str</span></p>
<p>The name of the Campaign.</p>

</dd>
<dt><h4><a name="attr_ba_Campaign__sequential">sequential</a></h4></dt><dd>
<p><span>bool</span></p>
<p>Whether this Campaign's levels must be played in sequence.</p>

</dd>
</dl>
<h3>Methods:</h3>
<h5><a href="#method_ba_Campaign____init__">&lt;constructor&gt;</a>, <a href="#method_ba_Campaign__addlevel">addlevel()</a>, <a href="#method_ba_Campaign__get_selected_level">get_selected_level()</a>, <a href="#method_ba_Campaign__getlevel">getlevel()</a>, <a href="#method_ba_Campaign__reset">reset()</a>, <a href="#method_ba_Campaign__set_selected_level">set_selected_level()</a></h5>
<dl>
<dt><h4><a name="method_ba_Campaign____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.Campaign(name: str, sequential: bool = True)</span></p>

</dd>
<dt><h4><a name="method_ba_Campaign__addlevel">addlevel()</a></dt></h4><dd>
<p><span>addlevel(self, level: <a href="#class_ba_Level">ba.Level</a>) -&gt; None</span></p>

<p>Adds a <a href="#class_ba_Level">ba.Level</a> to the Campaign.</p>

</dd>
<dt><h4><a name="method_ba_Campaign__get_selected_level">get_selected_level()</a></dt></h4><dd>
<p><span>get_selected_level(self) -&gt; str</span></p>

<p>Return the name of the Level currently selected in the UI.</p>

</dd>
<dt><h4><a name="method_ba_Campaign__getlevel">getlevel()</a></dt></h4><dd>
<p><span>getlevel(self, name: str) -&gt; <a href="#class_ba_Level">ba.Level</a></span></p>

<p>Return a contained <a href="#class_ba_Level">ba.Level</a> by name.</p>

</dd>
<dt><h4><a name="method_ba_Campaign__reset">reset()</a></dt></h4><dd>
<p><span>reset(self) -&gt; None</span></p>

<p>Reset state for the Campaign.</p>

</dd>
<dt><h4><a name="method_ba_Campaign__set_selected_level">set_selected_level()</a></dt></h4><dd>
<p><span>set_selected_level(self, levelname: str) -&gt; None</span></p>

<p>Set the Level currently selected in the UI (by name).</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_CelebrateMessage">ba.CelebrateMessage</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Tells an object to celebrate.</p>

<p>Category: <a href="#class_category_Message_Classes">Message Classes</a></p>

<h3>Attributes:</h3>
<dl>
<dt><h4><a name="attr_ba_CelebrateMessage__duration">duration</a></h4></dt><dd>
<p><span>float</span></p>
<p>Amount of time to celebrate in seconds.</p>

</dd>
</dl>
<h3>Methods:</h3>
<dl>
<dt><h4><a name="method_ba_CelebrateMessage____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.CelebrateMessage(duration: float = 10.0)</span></p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_ChoiceSetting">ba.ChoiceSetting</a></strong></h3>
<p>Inherits from: <a href="#class_ba_Setting">ba.Setting</a></p>
<p>A setting with multiple choices.</p>

<p>Category: <a href="#class_category_Settings_Classes">Settings Classes</a>
</p>

<h3>Methods:</h3>
<dl>
<dt><h4><a name="method_ba_ChoiceSetting____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.ChoiceSetting(name: str, default: Any, choices: List[Tuple[str, Any]])</span></p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_Chooser">ba.Chooser</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>A character/team selector for a <a href="#class_ba_Player">ba.Player</a>.</p>

<p>Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a>
</p>

<h3>Attributes:</h3>
<h5><a href="#attr_ba_Chooser__lobby">lobby</a>, <a href="#attr_ba_Chooser__ready">ready</a>, <a href="#attr_ba_Chooser__sessionplayer">sessionplayer</a>, <a href="#attr_ba_Chooser__sessionteam">sessionteam</a></h5>
<dl>
<dt><h4><a name="attr_ba_Chooser__lobby">lobby</a></h4></dt><dd>
<p><span><a href="#class_ba_Lobby">ba.Lobby</a></span></p>
<p>The chooser's <a href="#class_ba_Lobby">ba.Lobby</a>.</p>

</dd>
<dt><h4><a name="attr_ba_Chooser__ready">ready</a></h4></dt><dd>
<p><span>bool</span></p>
<p>Whether this chooser is checked in as ready.</p>

</dd>
<dt><h4><a name="attr_ba_Chooser__sessionplayer">sessionplayer</a></h4></dt><dd>
<p><span><a href="#class_ba_SessionPlayer">ba.SessionPlayer</a></span></p>
<p>The <a href="#class_ba_SessionPlayer">ba.SessionPlayer</a> associated with this chooser.</p>

</dd>
<dt><h4><a name="attr_ba_Chooser__sessionteam">sessionteam</a></h4></dt><dd>
<p><span><a href="#class_ba_SessionTeam">ba.SessionTeam</a></span></p>
<p>Return this chooser's currently selected <a href="#class_ba_SessionTeam">ba.SessionTeam</a>.</p>

</dd>
</dl>
<h3>Methods:</h3>
<h5><a href="#method_ba_Chooser____init__">&lt;constructor&gt;</a>, <a href="#method_ba_Chooser__get_character_name">get_character_name()</a>, <a href="#method_ba_Chooser__get_color">get_color()</a>, <a href="#method_ba_Chooser__get_highlight">get_highlight()</a>, <a href="#method_ba_Chooser__get_lobby">get_lobby()</a>, <a href="#method_ba_Chooser__getplayer">getplayer()</a>, <a href="#method_ba_Chooser__handlemessage">handlemessage()</a>, <a href="#method_ba_Chooser__reload_profiles">reload_profiles()</a>, <a href="#method_ba_Chooser__update_from_profile">update_from_profile()</a>, <a href="#method_ba_Chooser__update_position">update_position()</a></h5>
<dl>
<dt><h4><a name="method_ba_Chooser____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.Chooser(vpos: float, sessionplayer: _<a href="#class_ba_SessionPlayer">ba.SessionPlayer</a>, lobby: "Lobby")</span></p>

</dd>
<dt><h4><a name="method_ba_Chooser__get_character_name">get_character_name()</a></dt></h4><dd>
<p><span>get_character_name(self) -&gt; str</span></p>

<p>Return the selected character name.</p>

</dd>
<dt><h4><a name="method_ba_Chooser__get_color">get_color()</a></dt></h4><dd>
<p><span>get_color(self) -&gt; Sequence[float]</span></p>

<p>Return the currently selected color.</p>

</dd>
<dt><h4><a name="method_ba_Chooser__get_highlight">get_highlight()</a></dt></h4><dd>
<p><span>get_highlight(self) -&gt; Sequence[float]</span></p>

<p>Return the currently selected highlight.</p>

</dd>
<dt><h4><a name="method_ba_Chooser__get_lobby">get_lobby()</a></dt></h4><dd>
<p><span>get_lobby(self) -&gt; Optional[<a href="#class_ba_Lobby">ba.Lobby</a>]</span></p>

<p>Return this chooser's lobby if it still exists; otherwise None.</p>

</dd>
<dt><h4><a name="method_ba_Chooser__getplayer">getplayer()</a></dt></h4><dd>
<p><span>getplayer(self) -&gt; <a href="#class_ba_SessionPlayer">ba.SessionPlayer</a></span></p>

<p>Return the player associated with this chooser.</p>

</dd>
<dt><h4><a name="method_ba_Chooser__handlemessage">handlemessage()</a></dt></h4><dd>
<p><span>handlemessage(self, msg: Any) -&gt; Any</span></p>

<p>Standard generic message handler.</p>

</dd>
<dt><h4><a name="method_ba_Chooser__reload_profiles">reload_profiles()</a></dt></h4><dd>
<p><span>reload_profiles(self) -&gt; None</span></p>

<p>Reload all player profiles.</p>

</dd>
<dt><h4><a name="method_ba_Chooser__update_from_profile">update_from_profile()</a></dt></h4><dd>
<p><span>update_from_profile(self) -&gt; None</span></p>

<p>Set character/colors based on the current profile.</p>

</dd>
<dt><h4><a name="method_ba_Chooser__update_position">update_position()</a></dt></h4><dd>
<p><span>update_position(self) -&gt; None</span></p>

<p>Update this chooser's position.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_CollideModel">ba.CollideModel</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>A reference to a collide-model.</p>

<p>Category: <a href="#class_category_Asset_Classes">Asset Classes</a></p>

<p>Use <a href="#function_ba_getcollidemodel">ba.getcollidemodel</a>() to instantiate one.</p>

<hr>
<h2><strong><a name="class_ba_Collision">ba.Collision</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>A class providing info about occurring collisions.</p>

<p>Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a>
</p>

<h3>Attributes:</h3>
<h5><a href="#attr_ba_Collision__opposingbody">opposingbody</a>, <a href="#attr_ba_Collision__opposingnode">opposingnode</a>, <a href="#attr_ba_Collision__position">position</a>, <a href="#attr_ba_Collision__sourcenode">sourcenode</a></h5>
<dl>
<dt><h4><a name="attr_ba_Collision__opposingbody">opposingbody</a></h4></dt><dd>
<p><span>int</span></p>
<p>The body index on the opposing node in the current collision.</p>

</dd>
<dt><h4><a name="attr_ba_Collision__opposingnode">opposingnode</a></h4></dt><dd>
<p><span><a href="#class_ba_Node">ba.Node</a></span></p>
<p>The node the current callback material node is hitting.</p>

<p>        Throws a <a href="#class_ba_NodeNotFoundError">ba.NodeNotFoundError</a> if the node does not exist.
        This can be expected in some cases such as in 'disconnect'
        callbacks triggered by deleting a currently-colliding node.</p>

</dd>
<dt><h4><a name="attr_ba_Collision__position">position</a></h4></dt><dd>
<p><span><a href="#class_ba_Vec3">ba.Vec3</a></span></p>
<p>The position of the current collision.</p>

</dd>
<dt><h4><a name="attr_ba_Collision__sourcenode">sourcenode</a></h4></dt><dd>
<p><span><a href="#class_ba_Node">ba.Node</a></span></p>
<p>The node containing the material triggering the current callback.</p>

<p>        Throws a <a href="#class_ba_NodeNotFoundError">ba.NodeNotFoundError</a> if the node does not exist, though
        the node should always exist (at least at the start of the collision
        callback).</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_Context">ba.Context</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Context(source: Any)</p>

<p>A game context state.</p>

<p>Category: <a href="#class_category_General_Utility_Classes">General Utility Classes</a></p>

<p>Many operations such as <a href="#function_ba_newnode">ba.newnode</a>() or <a href="#function_ba_gettexture">ba.gettexture</a>() operate
implicitly on the current context. Each <a href="#class_ba_Activity">ba.Activity</a> has its own
Context and objects within that activity (nodes, media, etc) can only
interact with other objects from that context.</p>

<p>In general, as a modder, you should not need to worry about contexts,
since timers and other callbacks will take care of saving and
restoring the context automatically, but there may be rare cases where
you need to deal with them, such as when loading media in for use in
the UI (there is a special 'ui' context for all user-interface-related
functionality)</p>

<p>When instantiating a <a href="#class_ba_Context">ba.Context</a> instance, a single 'source' argument
is passed, which can be one of the following strings/objects:</p>

<p>'empty':
  Gives an empty context; it can be handy to run code here to ensure
  it does no loading of media, creation of nodes, etc.</p>

<p>'current':
  Sets the context object to the current context.</p>

<p>'ui':
  Sets to the UI context. UI functions as well as loading of media to
  be used in said functions must happen in the UI context.</p>

<p>A <a href="#class_ba_Activity">ba.Activity</a> instance:
  Gives the context for the provided <a href="#class_ba_Activity">ba.Activity</a>.
  Most all code run during a game happens in an Activity's Context.</p>

<p>A <a href="#class_ba_Session">ba.Session</a> instance:
  Gives the context for the provided <a href="#class_ba_Session">ba.Session</a>.
  Generally a user should not need to run anything here.</p>

<p><strong>
Usage:</strong></p>

<p>Contexts are generally used with the python 'with' statement, which
sets the context as current on entry and resets it to the previous
value on exit.</p>

<pre><span><em><small># Example: load a few textures into the UI context</small></em></span>
<span><em><small># (for use in widgets, etc):</small></em></span>
with <a href="#class_ba_Context">ba.Context</a>('ui'):
   tex1 = <a href="#function_ba_gettexture">ba.gettexture</a>('foo_tex_1')
   tex2 = <a href="#function_ba_gettexture">ba.gettexture</a>('foo_tex_2')</pre>

<hr>
<h2><strong><a name="class_ba_ContextCall">ba.ContextCall</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>ContextCall(call: Callable)</p>

<p>A context-preserving callable.</p>

<p>Category: <a href="#class_category_General_Utility_Classes">General Utility Classes</a></p>

<p>A ContextCall wraps a callable object along with a reference
to the current context (see <a href="#class_ba_Context">ba.Context</a>); it handles restoring the
context when run and automatically clears itself if the context
it belongs to shuts down.</p>

<p>Generally you should not need to use this directly; all standard
Ballistica callbacks involved with timers, materials, UI functions,
etc. handle this under-the-hood you don't have to worry about it.
The only time it may be necessary is if you are implementing your
own callbacks, such as a worker thread that does some action and then
runs some game code when done. By wrapping said callback in one of
these, you can ensure that you will not inadvertently be keeping the
current activity alive or running code in a torn-down (expired)
context.</p>

<p>You can also use <a href="#class_ba_WeakCall">ba.WeakCall</a> for similar functionality, but
ContextCall has the added bonus that it will not run during context
shutdown, whereas <a href="#class_ba_WeakCall">ba.WeakCall</a> simply looks at whether the target
object still exists.</p>

<pre><span><em><small># Example A: code like this can inadvertently prevent our activity</small></em></span>
<span><em><small># (self) from ending until the operation completes, since the bound</small></em></span>
<span><em><small># method we're passing (self.dosomething) contains a strong-reference</small></em></span>
<span><em><small># to self).</small></em></span>
start_some_long_action(callback_when_done=self.dosomething)</pre>

<pre><span><em><small># Example B: in this case our activity (self) can still die</small></em></span>
<span><em><small># properly; the callback will clear itself when the activity starts</small></em></span>
<span><em><small># shutting down, becoming a harmless no-op and releasing the reference</small></em></span>
<span><em><small># to our activity.</small></em></span>
start_long_action(callback_when_done=<a href="#class_ba_ContextCall">ba.ContextCall</a>(self.mycallback))</pre>

<hr>
<h2><strong><a name="class_ba_ContextError">ba.ContextError</a></strong></h3>
<p>Inherits from: <a href="https://docs.python.org/3/library/exceptions.html#Exception">Exception</a>, <a href="https://docs.python.org/3/library/exceptions.html#BaseException">BaseException</a></p>
<p>Exception raised when a call is made in an invalid context.</p>

<p>Category: <a href="#class_category_Exception_Classes">Exception Classes</a></p>

<p>    Examples of this include calling UI functions within an Activity context
    or calling scene manipulation functions outside of a game context.
</p>

<h3>Methods:</h3>
<p>&lt;all methods inherited from <a href="https://docs.python.org/3/library/exceptions.html#Exception">Exception</a>&gt;</p>
<hr>
<h2><strong><a name="class_ba_CoopGameActivity">ba.CoopGameActivity</a></strong></h3>
<p>Inherits from: <a href="#class_ba_GameActivity">ba.GameActivity</a>, <a href="#class_ba_Activity">ba.Activity</a>, <a href="#class_ba_DependencyComponent">ba.DependencyComponent</a>, <a href="https://docs.python.org/3/library/typing.html#typing.Generic">typing.Generic</a></p>
<p>Base class for cooperative-mode games.</p>

<p>Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a>
</p>

<h3>Attributes Inherited:</h3>
<h5><a href="#attr_ba_Activity__players">players</a>, <a href="#attr_ba_Activity__settings_raw">settings_raw</a>, <a href="#attr_ba_Activity__teams">teams</a></h5>
<h3>Attributes Defined Here:</h3>
<h5><a href="#attr_ba_CoopGameActivity__customdata">customdata</a>, <a href="#attr_ba_CoopGameActivity__expired">expired</a>, <a href="#attr_ba_CoopGameActivity__globalsnode">globalsnode</a>, <a href="#attr_ba_CoopGameActivity__map">map</a>, <a href="#attr_ba_CoopGameActivity__playertype">playertype</a>, <a href="#attr_ba_CoopGameActivity__session">session</a>, <a href="#attr_ba_CoopGameActivity__stats">stats</a>, <a href="#attr_ba_CoopGameActivity__teamtype">teamtype</a></h5>
<dl>
<dt><h4><a name="attr_ba_CoopGameActivity__customdata">customdata</a></h4></dt><dd>
<p><span>dict</span></p>
<p>Entities needing to store simple data with an activity can put it
        here. This dict will be deleted when the activity expires, so contained
        objects generally do not need to worry about handling expired
        activities.</p>

</dd>
<dt><h4><a name="attr_ba_CoopGameActivity__expired">expired</a></h4></dt><dd>
<p><span>bool</span></p>
<p>Whether the activity is expired.</p>

<p>        An activity is set as expired when shutting down.
        At this point no new nodes, timers, etc should be made,
        run, etc, and the activity should be considered a 'zombie'.</p>

</dd>
<dt><h4><a name="attr_ba_CoopGameActivity__globalsnode">globalsnode</a></h4></dt><dd>
<p><span><a href="#class_ba_Node">ba.Node</a></span></p>
<p>The 'globals' <a href="#class_ba_Node">ba.Node</a> for the activity. This contains various
        global controls and values.</p>

</dd>
<dt><h4><a name="attr_ba_CoopGameActivity__map">map</a></h4></dt><dd>
<p><span><a href="#class_ba_Map">ba.Map</a></span></p>
<p>The map being used for this game.</p>

<p>        Raises a <a href="#class_ba_NotFoundError">ba.NotFoundError</a> if the map does not currently exist.</p>

</dd>
<dt><h4><a name="attr_ba_CoopGameActivity__playertype">playertype</a></h4></dt><dd>
<p><span>Type[PlayerType]</span></p>
<p>The type of <a href="#class_ba_Player">ba.Player</a> this Activity is using.</p>

</dd>
<dt><h4><a name="attr_ba_CoopGameActivity__session">session</a></h4></dt><dd>
<p><span><a href="#class_ba_Session">ba.Session</a></span></p>
<p>The <a href="#class_ba_Session">ba.Session</a> this <a href="#class_ba_Activity">ba.Activity</a> belongs go.</p>

<p>        Raises a <a href="#class_ba_SessionNotFoundError">ba.SessionNotFoundError</a> if the Session no longer exists.</p>

</dd>
<dt><h4><a name="attr_ba_CoopGameActivity__stats">stats</a></h4></dt><dd>
<p><span><a href="#class_ba_Stats">ba.Stats</a></span></p>
<p>The stats instance accessible while the activity is running.</p>

<p>        If access is attempted before or after, raises a <a href="#class_ba_NotFoundError">ba.NotFoundError</a>.</p>

</dd>
<dt><h4><a name="attr_ba_CoopGameActivity__teamtype">teamtype</a></h4></dt><dd>
<p><span>Type[TeamType]</span></p>
<p>The type of <a href="#class_ba_Team">ba.Team</a> this Activity is using.</p>

</dd>
</dl>
<h3>Methods Inherited:</h3>
<h5><a href="#method_ba_GameActivity__add_actor_weak_ref">add_actor_weak_ref()</a>, <a href="#method_ba_GameActivity__add_player">add_player()</a>, <a href="#method_ba_GameActivity__add_team">add_team()</a>, <a href="#method_ba_GameActivity__begin">begin()</a>, <a href="#method_ba_GameActivity__continue_or_end_game">continue_or_end_game()</a>, <a href="#method_ba_GameActivity__create_player">create_player()</a>, <a href="#method_ba_GameActivity__create_settings_ui">create_settings_ui()</a>, <a href="#method_ba_GameActivity__create_team">create_team()</a>, <a href="#method_ba_GameActivity__dep_is_present">dep_is_present()</a>, <a href="#method_ba_GameActivity__end">end()</a>, <a href="#method_ba_GameActivity__end_game">end_game()</a>, <a href="#method_ba_GameActivity__expire">expire()</a>, <a href="#method_ba_GameActivity__get_available_settings">get_available_settings()</a>, <a href="#method_ba_GameActivity__get_description">get_description()</a>, <a href="#method_ba_GameActivity__get_description_display_string">get_description_display_string()</a>, <a href="#method_ba_GameActivity__get_display_string">get_display_string()</a>, <a href="#method_ba_GameActivity__get_dynamic_deps">get_dynamic_deps()</a>, <a href="#method_ba_GameActivity__get_instance_description">get_instance_description()</a>, <a href="#method_ba_GameActivity__get_instance_description_short">get_instance_description_short()</a>, <a href="#method_ba_GameActivity__get_instance_display_string">get_instance_display_string()</a>, <a href="#method_ba_GameActivity__get_instance_scoreboard_display_string">get_instance_scoreboard_display_string()</a>, <a href="#method_ba_GameActivity__get_settings_display_string">get_settings_display_string()</a>, <a href="#method_ba_GameActivity__get_supported_maps">get_supported_maps()</a>, <a href="#method_ba_GameActivity__get_team_display_string">get_team_display_string()</a>, <a href="#method_ba_GameActivity__getname">getname()</a>, <a href="#method_ba_GameActivity__getscoreconfig">getscoreconfig()</a>, <a href="#method_ba_GameActivity__handlemessage">handlemessage()</a>, <a href="#method_ba_GameActivity__has_begun">has_begun()</a>, <a href="#method_ba_GameActivity__has_ended">has_ended()</a>, <a href="#method_ba_GameActivity__has_transitioned_in">has_transitioned_in()</a>, <a href="#method_ba_GameActivity__is_transitioning_out">is_transitioning_out()</a>, <a href="#method_ba_GameActivity__is_waiting_for_continue">is_waiting_for_continue()</a>, <a href="#method_ba_GameActivity__on_continue">on_continue()</a>, <a href="#method_ba_GameActivity__on_expire">on_expire()</a>, <a href="#method_ba_GameActivity__on_player_join">on_player_join()</a>, <a href="#method_ba_GameActivity__on_player_leave">on_player_leave()</a>, <a href="#method_ba_GameActivity__on_team_join">on_team_join()</a>, <a href="#method_ba_GameActivity__on_team_leave">on_team_leave()</a>, <a href="#method_ba_GameActivity__on_transition_in">on_transition_in()</a>, <a href="#method_ba_GameActivity__on_transition_out">on_transition_out()</a>, <a href="#method_ba_GameActivity__remove_player">remove_player()</a>, <a href="#method_ba_GameActivity__remove_team">remove_team()</a>, <a href="#method_ba_GameActivity__respawn_player">respawn_player()</a>, <a href="#method_ba_GameActivity__retain_actor">retain_actor()</a>, <a href="#method_ba_GameActivity__set_has_ended">set_has_ended()</a>, <a href="#method_ba_GameActivity__setup_standard_powerup_drops">setup_standard_powerup_drops()</a>, <a href="#method_ba_GameActivity__setup_standard_time_limit">setup_standard_time_limit()</a>, <a href="#method_ba_GameActivity__show_zoom_message">show_zoom_message()</a>, <a href="#method_ba_GameActivity__spawn_player">spawn_player()</a>, <a href="#method_ba_GameActivity__spawn_player_if_exists">spawn_player_if_exists()</a>, <a href="#method_ba_GameActivity__transition_in">transition_in()</a>, <a href="#method_ba_GameActivity__transition_out">transition_out()</a></h5>
<h3>Methods Defined or Overridden:</h3>
<h5><a href="#method_ba_CoopGameActivity____init__">&lt;constructor&gt;</a>, <a href="#method_ba_CoopGameActivity__celebrate">celebrate()</a>, <a href="#method_ba_CoopGameActivity__fade_to_red">fade_to_red()</a>, <a href="#method_ba_CoopGameActivity__get_score_type">get_score_type()</a>, <a href="#method_ba_CoopGameActivity__on_begin">on_begin()</a>, <a href="#method_ba_CoopGameActivity__setup_low_life_warning_sound">setup_low_life_warning_sound()</a>, <a href="#method_ba_CoopGameActivity__spawn_player_spaz">spawn_player_spaz()</a>, <a href="#method_ba_CoopGameActivity__supports_session_type">supports_session_type()</a></h5>
<dl>
<dt><h4><a name="method_ba_CoopGameActivity____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.CoopGameActivity(settings: dict)</span></p>

<p>Instantiate the Activity.</p>

</dd>
<dt><h4><a name="method_ba_CoopGameActivity__celebrate">celebrate()</a></dt></h4><dd>
<p><span>celebrate(self, duration: float) -&gt; None</span></p>

<p>Tells all existing player-controlled characters to celebrate.</p>

<p>Can be useful in co-op games when the good guys score or complete
a wave.
duration is given in seconds.</p>

</dd>
<dt><h4><a name="method_ba_CoopGameActivity__fade_to_red">fade_to_red()</a></dt></h4><dd>
<p><span>fade_to_red(self) -&gt; None</span></p>

<p>Fade the screen to red; (such as when the good guys have lost).</p>

</dd>
<dt><h4><a name="method_ba_CoopGameActivity__get_score_type">get_score_type()</a></dt></h4><dd>
<p><span>get_score_type(self) -&gt; str</span></p>

<p>Return the score unit this co-op game uses ('point', 'seconds', etc.)</p>

</dd>
<dt><h4><a name="method_ba_CoopGameActivity__on_begin">on_begin()</a></dt></h4><dd>
<p><span>on_begin(self) -&gt; None</span></p>

<p>Called once the previous <a href="#class_ba_Activity">ba.Activity</a> has finished transitioning out.</p>

<p>At this point the activity's initial players and teams are filled in
and it should begin its actual game logic.</p>

</dd>
<dt><h4><a name="method_ba_CoopGameActivity__setup_low_life_warning_sound">setup_low_life_warning_sound()</a></dt></h4><dd>
<p><span>setup_low_life_warning_sound(self) -&gt; None</span></p>

<p>Set up a beeping noise to play when any players are near death.</p>

</dd>
<dt><h4><a name="method_ba_CoopGameActivity__spawn_player_spaz">spawn_player_spaz()</a></dt></h4><dd>
<p><span>spawn_player_spaz(self, player: PlayerType, position: Sequence[float] = (0.0, 0.0, 0.0), angle: float = None) -&gt; PlayerSpaz</span></p>

<p>Spawn and wire up a standard player spaz.</p>

</dd>
<dt><h4><a name="method_ba_CoopGameActivity__supports_session_type">supports_session_type()</a></dt></h4><dd>
<h5><span><em>&lt;class method&gt;</span></em></h5>
<p><span>supports_session_type(sessiontype: Type[<a href="#class_ba_Session">ba.Session</a>]) -&gt; bool </span></p>

<p>Return whether this game supports the provided Session type.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_CoopSession">ba.CoopSession</a></strong></h3>
<p>Inherits from: <a href="#class_ba_Session">ba.Session</a></p>
<p>A <a href="#class_ba_Session">ba.Session</a> which runs cooperative-mode games.</p>

<p>Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a></p>

<p>    These generally consist of 1-4 players against
    the computer and include functionality such as
    high score lists.</p>

<h3>Attributes Inherited:</h3>
<h5><a href="#attr_ba_Session__allow_mid_activity_joins">allow_mid_activity_joins</a>, <a href="#attr_ba_Session__customdata">customdata</a>, <a href="#attr_ba_Session__lobby">lobby</a>, <a href="#attr_ba_Session__max_players">max_players</a>, <a href="#attr_ba_Session__min_players">min_players</a>, <a href="#attr_ba_Session__sessionplayers">sessionplayers</a>, <a href="#attr_ba_Session__sessionteams">sessionteams</a>, <a href="#attr_ba_Session__use_team_colors">use_team_colors</a>, <a href="#attr_ba_Session__use_teams">use_teams</a></h5>
<h3>Attributes Defined Here:</h3>
<h5><a href="#attr_ba_CoopSession__campaign">campaign</a>, <a href="#attr_ba_CoopSession__sessionglobalsnode">sessionglobalsnode</a></h5>
<dl>
<dt><h4><a name="attr_ba_CoopSession__campaign">campaign</a></h4></dt><dd>
<p><span>Optional[<a href="#class_ba_Campaign">ba.Campaign</a>]</span></p>
<p>The <a href="#class_ba_Campaign">ba.Campaign</a> instance this Session represents, or None if
there is no associated Campaign.</p>

</dd>
<dt><h4><a name="attr_ba_CoopSession__sessionglobalsnode">sessionglobalsnode</a></h4></dt><dd>
<p><span><a href="#class_ba_Node">ba.Node</a></span></p>
<p>The sessionglobals <a href="#class_ba_Node">ba.Node</a> for the session.</p>

</dd>
</dl>
<h3>Methods Inherited:</h3>
<h5><a href="#method_ba_Session__begin_next_activity">begin_next_activity()</a>, <a href="#method_ba_Session__end">end()</a>, <a href="#method_ba_Session__end_activity">end_activity()</a>, <a href="#method_ba_Session__getactivity">getactivity()</a>, <a href="#method_ba_Session__handlemessage">handlemessage()</a>, <a href="#method_ba_Session__on_player_request">on_player_request()</a>, <a href="#method_ba_Session__on_team_join">on_team_join()</a>, <a href="#method_ba_Session__on_team_leave">on_team_leave()</a>, <a href="#method_ba_Session__setactivity">setactivity()</a>, <a href="#method_ba_Session__transitioning_out_activity_was_freed">transitioning_out_activity_was_freed()</a></h5>
<h3>Methods Defined or Overridden:</h3>
<h5><a href="#method_ba_CoopSession____init__">&lt;constructor&gt;</a>, <a href="#method_ba_CoopSession__get_current_game_instance">get_current_game_instance()</a>, <a href="#method_ba_CoopSession__get_custom_menu_entries">get_custom_menu_entries()</a>, <a href="#method_ba_CoopSession__on_activity_end">on_activity_end()</a>, <a href="#method_ba_CoopSession__on_player_leave">on_player_leave()</a>, <a href="#method_ba_CoopSession__restart">restart()</a></h5>
<dl>
<dt><h4><a name="method_ba_CoopSession____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.CoopSession()</span></p>

<p>Instantiate a co-op mode session.</p>

</dd>
<dt><h4><a name="method_ba_CoopSession__get_current_game_instance">get_current_game_instance()</a></dt></h4><dd>
<p><span>get_current_game_instance(self) -&gt; <a href="#class_ba_GameActivity">ba.GameActivity</a></span></p>

<p>Get the game instance currently being played.</p>

</dd>
<dt><h4><a name="method_ba_CoopSession__get_custom_menu_entries">get_custom_menu_entries()</a></dt></h4><dd>
<p><span>get_custom_menu_entries(self) -&gt; List[Dict[str, Any]]</span></p>

<p>Subclasses can override this to provide custom menu entries.</p>

<p>The returned value should be a list of dicts, each containing
a 'label' and 'call' entry, with 'label' being the text for
the entry and 'call' being the callable to trigger if the entry
is pressed.</p>

</dd>
<dt><h4><a name="method_ba_CoopSession__on_activity_end">on_activity_end()</a></dt></h4><dd>
<p><span>on_activity_end(self, activity: <a href="#class_ba_Activity">ba.Activity</a>, results: Any) -&gt; None</span></p>

<p>Method override for co-op sessions.</p>

<p>Jumps between co-op games and score screens.</p>

</dd>
<dt><h4><a name="method_ba_CoopSession__on_player_leave">on_player_leave()</a></dt></h4><dd>
<p><span>on_player_leave(self, sessionplayer: <a href="#class_ba_SessionPlayer">ba.SessionPlayer</a>) -&gt; None</span></p>

<p>Called when a previously-accepted <a href="#class_ba_SessionPlayer">ba.SessionPlayer</a> leaves.</p>

</dd>
<dt><h4><a name="method_ba_CoopSession__restart">restart()</a></dt></h4><dd>
<p><span>restart(self) -&gt; None</span></p>

<p>Restart the current game activity.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_Data">ba.Data</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>A reference to a data object.</p>

<p>Category: <a href="#class_category_Asset_Classes">Asset Classes</a></p>

<p>Use ba.getdata() to instantiate one.</p>

<h3>Methods:</h3>
<dl>
<dt><h4><a name="method_ba_Data__getvalue">getvalue()</a></dt></h4><dd>
<p><span>getvalue() -&gt; Any</span></p>

<p>Return the data object's value.</p>

<p>This can consist of anything representable by json (dicts, lists,
numbers, bools, None, etc).
Note that this call will block if the data has not yet been loaded,
so it can be beneficial to plan a short bit of time between when
the data object is requested and when it's value is accessed.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_DeathType">ba.DeathType</a></strong></h3>
<p>Inherits from: <a href="https://docs.python.org/3/library/enum.html#enum.Enum">enum.Enum</a></p>
<p>A reason for a death.</p>

<p>Category: <a href="#class_category_Enums">Enums</a>
</p>

<h3>Values:</h3>
<ul>
<li>GENERIC</li>
<li>OUT_OF_BOUNDS</li>
<li>IMPACT</li>
<li>FALL</li>
<li>REACHED_GOAL</li>
<li>LEFT_GAME</li>
</ul>
<hr>
<h2><strong><a name="class_ba_DelegateNotFoundError">ba.DelegateNotFoundError</a></strong></h3>
<p>Inherits from: <a href="#class_ba_NotFoundError">ba.NotFoundError</a>, <a href="https://docs.python.org/3/library/exceptions.html#Exception">Exception</a>, <a href="https://docs.python.org/3/library/exceptions.html#BaseException">BaseException</a></p>
<p>Exception raised when an expected delegate object does not exist.</p>

<p>Category: <a href="#class_category_Exception_Classes">Exception Classes</a>
</p>

<h3>Methods:</h3>
<p>&lt;all methods inherited from <a href="#class_ba_NotFoundError">ba.NotFoundError</a>&gt;</p>
<hr>
<h2><strong><a name="class_ba_Dependency">ba.Dependency</a></strong></h3>
<p>Inherits from: <a href="https://docs.python.org/3/library/typing.html#typing.Generic">typing.Generic</a></p>
<p>A dependency on a DependencyComponent (with an optional config).</p>

<p>Category: <a href="#class_category_Dependency_Classes">Dependency Classes</a></p>

<p>    This class is used to request and access functionality provided
    by other DependencyComponent classes from a DependencyComponent class.
    The class functions as a descriptor, allowing dependencies to
    be added at a class level much the same as properties or methods
    and then used with class instances to access those dependencies.
    For instance, if you do 'floofcls = <a href="#class_ba_Dependency">ba.Dependency</a>(FloofClass)' you
    would then be able to instantiate a FloofClass in your class's
    methods via self.floofcls().
</p>

<h3>Methods:</h3>
<h5><a href="#method_ba_Dependency____init__">&lt;constructor&gt;</a>, <a href="#method_ba_Dependency__get_hash">get_hash()</a></h5>
<dl>
<dt><h4><a name="method_ba_Dependency____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.Dependency(cls: Type[T], config: Any = None)</span></p>

<p>Instantiate a Dependency given a <a href="#class_ba_DependencyComponent">ba.DependencyComponent</a> type.</p>

<p>Optionally, an arbitrary object can be passed as 'config' to
influence dependency calculation for the target class.</p>

</dd>
<dt><h4><a name="method_ba_Dependency__get_hash">get_hash()</a></dt></h4><dd>
<p><span>get_hash(self) -&gt; int</span></p>

<p>Return the dependency's hash, calculating it if necessary.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_DependencyComponent">ba.DependencyComponent</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Base class for all classes that can act as or use dependencies.</p>

<p>Category: <a href="#class_category_Dependency_Classes">Dependency Classes</a>
</p>

<h3>Methods:</h3>
<h5><a href="#method_ba_DependencyComponent____init__">&lt;constructor&gt;</a>, <a href="#method_ba_DependencyComponent__dep_is_present">dep_is_present()</a>, <a href="#method_ba_DependencyComponent__get_dynamic_deps">get_dynamic_deps()</a></h5>
<dl>
<dt><h4><a name="method_ba_DependencyComponent____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.DependencyComponent()</span></p>

<p>Instantiate a DependencyComponent.</p>

</dd>
<dt><h4><a name="method_ba_DependencyComponent__dep_is_present">dep_is_present()</a></dt></h4><dd>
<h5><span><em>&lt;class method&gt;</span></em></h5>
<p><span>dep_is_present(config: Any = None) -&gt; bool </span></p>

<p>Return whether this component/config is present on this device.</p>

</dd>
<dt><h4><a name="method_ba_DependencyComponent__get_dynamic_deps">get_dynamic_deps()</a></dt></h4><dd>
<h5><span><em>&lt;class method&gt;</span></em></h5>
<p><span>get_dynamic_deps(config: Any = None) -&gt; List[Dependency] </span></p>

<p>Return any dynamically-calculated deps for this component/config.</p>

<p>Deps declared statically as part of the class do not need to be
included here; this is only for additional deps that may vary based
on the dep config value. (for instance a map required by a game type)</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_DependencyError">ba.DependencyError</a></strong></h3>
<p>Inherits from: <a href="https://docs.python.org/3/library/exceptions.html#Exception">Exception</a>, <a href="https://docs.python.org/3/library/exceptions.html#BaseException">BaseException</a></p>
<p>Exception raised when one or more <a href="#class_ba_Dependency">ba.Dependency</a> items are missing.</p>

<p>Category: <a href="#class_category_Exception_Classes">Exception Classes</a></p>

<p>    (this will generally be missing assets).
</p>

<h3>Attributes:</h3>
<dl>
<dt><h4><a name="attr_ba_DependencyError__deps">deps</a></h4></dt><dd>
<p><span>List[<a href="#class_ba_Dependency">ba.Dependency</a>]</span></p>
<p>The list of missing dependencies causing this error.</p>

</dd>
</dl>
<h3>Methods Inherited:</h3>
<h5><a href="#method_builtins_Exception__with_traceback">with_traceback()</a></h5>
<h3>Methods Defined or Overridden:</h3>
<dl>
<dt><h4><a name="method_ba_DependencyError____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.DependencyError(deps: List[<a href="#class_ba_Dependency">ba.Dependency</a>])</span></p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_DependencySet">ba.DependencySet</a></strong></h3>
<p>Inherits from: <a href="https://docs.python.org/3/library/typing.html#typing.Generic">typing.Generic</a></p>
<p>Set of resolved dependencies and their associated data.</p>

<p>Category: <a href="#class_category_Dependency_Classes">Dependency Classes</a></p>

<p>    To use DependencyComponents, a set must be created, resolved, and then
    loaded. The DependencyComponents are only valid while the set remains
    in existence.
</p>

<h3>Attributes:</h3>
<h5><a href="#attr_ba_DependencySet__resolved">resolved</a>, <a href="#attr_ba_DependencySet__root">root</a></h5>
<dl>
<dt><h4><a name="attr_ba_DependencySet__resolved">resolved</a></h4></dt><dd>
<p><span>bool</span></p>
<p>Whether this set has been successfully resolved.</p>

</dd>
<dt><h4><a name="attr_ba_DependencySet__root">root</a></h4></dt><dd>
<p><span>T</span></p>
<p>The instantiated root DependencyComponent instance for the set.</p>

</dd>
</dl>
<h3>Methods:</h3>
<h5><a href="#method_ba_DependencySet____init__">&lt;constructor&gt;</a>, <a href="#method_ba_DependencySet__get_asset_package_ids">get_asset_package_ids()</a>, <a href="#method_ba_DependencySet__load">load()</a>, <a href="#method_ba_DependencySet__resolve">resolve()</a></h5>
<dl>
<dt><h4><a name="method_ba_DependencySet____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.DependencySet(root_dependency: Dependency[T])</span></p>

</dd>
<dt><h4><a name="method_ba_DependencySet__get_asset_package_ids">get_asset_package_ids()</a></dt></h4><dd>
<p><span>get_asset_package_ids(self) -&gt; Set[str]</span></p>

<p>Return the set of asset-package-ids required by this dep-set.</p>

<p>Must be called on a resolved dep-set.</p>

</dd>
<dt><h4><a name="method_ba_DependencySet__load">load()</a></dt></h4><dd>
<p><span>load(self) -&gt; None</span></p>

<p>Instantiate all DependencyComponents in the set.</p>

<p>Returns a wrapper which can be used to instantiate the root dep.</p>

</dd>
<dt><h4><a name="method_ba_DependencySet__resolve">resolve()</a></dt></h4><dd>
<p><span>resolve(self) -&gt; None</span></p>

<p>Resolve the complete set of required dependencies for this set.</p>

<p>Raises a <a href="#class_ba_DependencyError">ba.DependencyError</a> if dependencies are missing (or other
Exception types on other errors).</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_DieMessage">ba.DieMessage</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>A message telling an object to die.</p>

<p>Category: <a href="#class_category_Message_Classes">Message Classes</a></p>

<p>    Most <a href="#class_ba_Actor">ba.Actors</a> respond to this.</p>

<h3>Attributes:</h3>
<h5><a href="#attr_ba_DieMessage__how">how</a>, <a href="#attr_ba_DieMessage__immediate">immediate</a></h5>
<dl>
<dt><h4><a name="attr_ba_DieMessage__how">how</a></h4></dt><dd>
<p><span>DeathType</span></p>
<p>The particular reason for death.</p>

</dd>
<dt><h4><a name="attr_ba_DieMessage__immediate">immediate</a></h4></dt><dd>
<p><span>bool</span></p>
<p>If this is set to True, the actor should disappear immediately.
This is for 'removing' stuff from the game more so than 'killing'
it. If False, the actor should die a 'normal' death and can take
its time with lingering corpses, sound effects, etc.</p>

</dd>
</dl>
<h3>Methods:</h3>
<dl>
<dt><h4><a name="method_ba_DieMessage____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.DieMessage(immediate: bool = False, how: DeathType = &lt;DeathType.GENERIC: generic&gt;)</span></p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_DropMessage">ba.DropMessage</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Tells an object that it has dropped what it was holding.</p>

<p>Category: <a href="#class_category_Message_Classes">Message Classes</a>
</p>

<h3>Methods:</h3>
<dl>
<dt><h4><a name="method_ba_DropMessage____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.DropMessage()</span></p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_DroppedMessage">ba.DroppedMessage</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Tells an object that it has been dropped.</p>

<p>Category: <a href="#class_category_Message_Classes">Message Classes</a></p>

<h3>Attributes:</h3>
<dl>
<dt><h4><a name="attr_ba_DroppedMessage__node">node</a></h4></dt><dd>
<p><span><a href="#class_ba_Node">ba.Node</a></span></p>
<p>The <a href="#class_ba_Node">ba.Node</a> doing the dropping.</p>

</dd>
</dl>
<h3>Methods:</h3>
<dl>
<dt><h4><a name="method_ba_DroppedMessage____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.DroppedMessage(node: <a href="#class_ba_Node">ba.Node</a>)</span></p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_DualTeamSession">ba.DualTeamSession</a></strong></h3>
<p>Inherits from: <a href="#class_ba_MultiTeamSession">ba.MultiTeamSession</a>, <a href="#class_ba_Session">ba.Session</a></p>
<p><a href="#class_ba_Session">ba.Session</a> type for teams mode games.</p>

<p>Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a>
</p>

<h3>Attributes Inherited:</h3>
<h5><a href="#attr_ba_Session__allow_mid_activity_joins">allow_mid_activity_joins</a>, <a href="#attr_ba_Session__customdata">customdata</a>, <a href="#attr_ba_Session__lobby">lobby</a>, <a href="#attr_ba_Session__max_players">max_players</a>, <a href="#attr_ba_Session__min_players">min_players</a>, <a href="#attr_ba_Session__sessionplayers">sessionplayers</a>, <a href="#attr_ba_Session__sessionteams">sessionteams</a>, <a href="#attr_ba_Session__use_team_colors">use_team_colors</a>, <a href="#attr_ba_Session__use_teams">use_teams</a></h5>
<h3>Attributes Defined Here:</h3>
<dl>
<dt><h4><a name="attr_ba_DualTeamSession__sessionglobalsnode">sessionglobalsnode</a></h4></dt><dd>
<p><span><a href="#class_ba_Node">ba.Node</a></span></p>
<p>The sessionglobals <a href="#class_ba_Node">ba.Node</a> for the session.</p>

</dd>
</dl>
<h3>Methods Inherited:</h3>
<h5><a href="#method_ba_MultiTeamSession__announce_game_results">announce_game_results()</a>, <a href="#method_ba_MultiTeamSession__begin_next_activity">begin_next_activity()</a>, <a href="#method_ba_MultiTeamSession__end">end()</a>, <a href="#method_ba_MultiTeamSession__end_activity">end_activity()</a>, <a href="#method_ba_MultiTeamSession__get_custom_menu_entries">get_custom_menu_entries()</a>, <a href="#method_ba_MultiTeamSession__get_ffa_series_length">get_ffa_series_length()</a>, <a href="#method_ba_MultiTeamSession__get_game_number">get_game_number()</a>, <a href="#method_ba_MultiTeamSession__get_max_players">get_max_players()</a>, <a href="#method_ba_MultiTeamSession__get_next_game_description">get_next_game_description()</a>, <a href="#method_ba_MultiTeamSession__get_series_length">get_series_length()</a>, <a href="#method_ba_MultiTeamSession__getactivity">getactivity()</a>, <a href="#method_ba_MultiTeamSession__handlemessage">handlemessage()</a>, <a href="#method_ba_MultiTeamSession__on_activity_end">on_activity_end()</a>, <a href="#method_ba_MultiTeamSession__on_player_leave">on_player_leave()</a>, <a href="#method_ba_MultiTeamSession__on_player_request">on_player_request()</a>, <a href="#method_ba_MultiTeamSession__on_team_join">on_team_join()</a>, <a href="#method_ba_MultiTeamSession__on_team_leave">on_team_leave()</a>, <a href="#method_ba_MultiTeamSession__setactivity">setactivity()</a>, <a href="#method_ba_MultiTeamSession__transitioning_out_activity_was_freed">transitioning_out_activity_was_freed()</a></h5>
<h3>Methods Defined or Overridden:</h3>
<dl>
<dt><h4><a name="method_ba_DualTeamSession____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.DualTeamSession()</span></p>

<p>Set up playlists and launches a <a href="#class_ba_Activity">ba.Activity</a> to accept joiners.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_EmptyPlayer">ba.EmptyPlayer</a></strong></h3>
<p>Inherits from: <a href="#class_ba_Player">ba.Player</a>, <a href="https://docs.python.org/3/library/typing.html#typing.Generic">typing.Generic</a></p>
<p>An empty player for use by Activities that don't need to define one.</p>

<p>Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a></p>

<p>    <a href="#class_ba_Player">ba.Player</a> and <a href="#class_ba_Team">ba.Team</a> are 'Generic' types, and so passing those top level
    classes as type arguments when defining a <a href="#class_ba_Activity">ba.Activity</a> reduces type safety.
    For example, activity.teams[0].player will have type 'Any' in that case.
    For that reason, it is better to pass EmptyPlayer and EmptyTeam when
    defining a <a href="#class_ba_Activity">ba.Activity</a> that does not need custom types of its own.</p>

<p>    Note that EmptyPlayer defines its team type as EmptyTeam and vice versa,
    so if you want to define your own class for one of them you should do so
    for both.
</p>

<h3>Attributes Inherited:</h3>
<h5><a href="#attr_ba_Player__actor">actor</a></h5>
<h3>Attributes Defined Here:</h3>
<h5><a href="#attr_ba_EmptyPlayer__customdata">customdata</a>, <a href="#attr_ba_EmptyPlayer__node">node</a>, <a href="#attr_ba_EmptyPlayer__position">position</a>, <a href="#attr_ba_EmptyPlayer__sessionplayer">sessionplayer</a>, <a href="#attr_ba_EmptyPlayer__team">team</a></h5>
<dl>
<dt><h4><a name="attr_ba_EmptyPlayer__customdata">customdata</a></h4></dt><dd>
<p><span>dict</span></p>
<p>Arbitrary values associated with the player.
        Though it is encouraged that most player values be properly defined
        on the <a href="#class_ba_Player">ba.Player</a> subclass, it may be useful for player-agnostic
        objects to store values here. This dict is cleared when the player
        leaves or expires so objects stored here will be disposed of at
        the expected time, unlike the Player instance itself which may
        continue to be referenced after it is no longer part of the game.</p>

</dd>
<dt><h4><a name="attr_ba_EmptyPlayer__node">node</a></h4></dt><dd>
<p><span><a href="#class_ba_Node">ba.Node</a></span></p>
<p>A <a href="#class_ba_Node">ba.Node</a> of type 'player' associated with this Player.</p>

<p>        This node can be used to get a generic player position/etc.</p>

</dd>
<dt><h4><a name="attr_ba_EmptyPlayer__position">position</a></h4></dt><dd>
<p><span><a href="#class_ba_Vec3">ba.Vec3</a></span></p>
<p>The position of the player, as defined by its current <a href="#class_ba_Actor">ba.Actor</a>.</p>

<p>        If the player currently has no actor, raises a <a href="#class_ba_ActorNotFoundError">ba.ActorNotFoundError</a>.</p>

</dd>
<dt><h4><a name="attr_ba_EmptyPlayer__sessionplayer">sessionplayer</a></h4></dt><dd>
<p><span><a href="#class_ba_SessionPlayer">ba.SessionPlayer</a></span></p>
<p>Return the <a href="#class_ba_SessionPlayer">ba.SessionPlayer</a> corresponding to this Player.</p>

<p>        Throws a <a href="#class_ba_SessionPlayerNotFoundError">ba.SessionPlayerNotFoundError</a> if it does not exist.</p>

</dd>
<dt><h4><a name="attr_ba_EmptyPlayer__team">team</a></h4></dt><dd>
<p><span>TeamType</span></p>
<p>The <a href="#class_ba_Team">ba.Team</a> for this player.</p>

</dd>
</dl>
<h3>Methods:</h3>
<p>&lt;all methods inherited from <a href="#class_ba_Player">ba.Player</a>&gt;</p>
<hr>
<h2><strong><a name="class_ba_EmptyTeam">ba.EmptyTeam</a></strong></h3>
<p>Inherits from: <a href="#class_ba_Team">ba.Team</a>, <a href="https://docs.python.org/3/library/typing.html#typing.Generic">typing.Generic</a></p>
<p>An empty player for use by Activities that don't need to define one.</p>

<p>Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a></p>

<p>    <a href="#class_ba_Player">ba.Player</a> and <a href="#class_ba_Team">ba.Team</a> are 'Generic' types, and so passing those top level
    classes as type arguments when defining a <a href="#class_ba_Activity">ba.Activity</a> reduces type safety.
    For example, activity.teams[0].player will have type 'Any' in that case.
    For that reason, it is better to pass EmptyPlayer and EmptyTeam when
    defining a <a href="#class_ba_Activity">ba.Activity</a> that does not need custom types of its own.</p>

<p>    Note that EmptyPlayer defines its team type as EmptyTeam and vice versa,
    so if you want to define your own class for one of them you should do so
    for both.
</p>

<h3>Attributes:</h3>
<h5><a href="#attr_ba_EmptyTeam__customdata">customdata</a>, <a href="#attr_ba_EmptyTeam__sessionteam">sessionteam</a></h5>
<dl>
<dt><h4><a name="attr_ba_EmptyTeam__customdata">customdata</a></h4></dt><dd>
<p><span>dict</span></p>
<p>Arbitrary values associated with the team.
        Though it is encouraged that most player values be properly defined
        on the <a href="#class_ba_Team">ba.Team</a> subclass, it may be useful for player-agnostic
        objects to store values here. This dict is cleared when the team
        leaves or expires so objects stored here will be disposed of at
        the expected time, unlike the Team instance itself which may
        continue to be referenced after it is no longer part of the game.</p>

</dd>
<dt><h4><a name="attr_ba_EmptyTeam__sessionteam">sessionteam</a></h4></dt><dd>
<p><span>SessionTeam</span></p>
<p>Return the <a href="#class_ba_SessionTeam">ba.SessionTeam</a> corresponding to this Team.</p>

<p>        Throws a <a href="#class_ba_SessionTeamNotFoundError">ba.SessionTeamNotFoundError</a> if there is none.</p>

</dd>
</dl>
<h3>Methods:</h3>
<p>&lt;all methods inherited from <a href="#class_ba_Team">ba.Team</a>&gt;</p>
<hr>
<h2><strong><a name="class_ba_Existable">ba.Existable</a></strong></h3>
<p>Inherits from: <a href="https://docs.python.org/3/library/typing.html#typing.Protocol">typing.Protocol</a>, <a href="https://docs.python.org/3/library/typing.html#typing.Generic">typing.Generic</a></p>
<p>A Protocol for objects supporting an exists() method.</p>

<p>Category: <a href="#class_category_Protocols">Protocols</a>
</p>

<h3>Methods:</h3>
<dl>
<dt><h4><a name="method_ba_Existable__exists">exists()</a></dt></h4><dd>
<p><span>exists(self) -&gt; bool</span></p>

<p>Whether this object exists.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_FloatChoiceSetting">ba.FloatChoiceSetting</a></strong></h3>
<p>Inherits from: <a href="#class_ba_ChoiceSetting">ba.ChoiceSetting</a>, <a href="#class_ba_Setting">ba.Setting</a></p>
<p>A float setting with multiple choices.</p>

<p>Category: <a href="#class_category_Settings_Classes">Settings Classes</a>
</p>

<h3>Methods:</h3>
<dl>
<dt><h4><a name="method_ba_FloatChoiceSetting____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.FloatChoiceSetting(name: str, default: float, choices: List[Tuple[str, float]])</span></p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_FloatSetting">ba.FloatSetting</a></strong></h3>
<p>Inherits from: <a href="#class_ba_Setting">ba.Setting</a></p>
<p>A floating point game setting.</p>

<p>Category: <a href="#class_category_Settings_Classes">Settings Classes</a>
</p>

<h3>Methods:</h3>
<dl>
<dt><h4><a name="method_ba_FloatSetting____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.FloatSetting(name: str, default: float, min_value: float = 0.0, max_value: float = 9999.0, increment: float = 1.0)</span></p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_FreeForAllSession">ba.FreeForAllSession</a></strong></h3>
<p>Inherits from: <a href="#class_ba_MultiTeamSession">ba.MultiTeamSession</a>, <a href="#class_ba_Session">ba.Session</a></p>
<p><a href="#class_ba_Session">ba.Session</a> type for free-for-all mode games.</p>

<p>Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a>
</p>

<h3>Attributes Inherited:</h3>
<h5><a href="#attr_ba_Session__allow_mid_activity_joins">allow_mid_activity_joins</a>, <a href="#attr_ba_Session__customdata">customdata</a>, <a href="#attr_ba_Session__lobby">lobby</a>, <a href="#attr_ba_Session__max_players">max_players</a>, <a href="#attr_ba_Session__min_players">min_players</a>, <a href="#attr_ba_Session__sessionplayers">sessionplayers</a>, <a href="#attr_ba_Session__sessionteams">sessionteams</a>, <a href="#attr_ba_Session__use_team_colors">use_team_colors</a>, <a href="#attr_ba_Session__use_teams">use_teams</a></h5>
<h3>Attributes Defined Here:</h3>
<dl>
<dt><h4><a name="attr_ba_FreeForAllSession__sessionglobalsnode">sessionglobalsnode</a></h4></dt><dd>
<p><span><a href="#class_ba_Node">ba.Node</a></span></p>
<p>The sessionglobals <a href="#class_ba_Node">ba.Node</a> for the session.</p>

</dd>
</dl>
<h3>Methods Inherited:</h3>
<h5><a href="#method_ba_MultiTeamSession__announce_game_results">announce_game_results()</a>, <a href="#method_ba_MultiTeamSession__begin_next_activity">begin_next_activity()</a>, <a href="#method_ba_MultiTeamSession__end">end()</a>, <a href="#method_ba_MultiTeamSession__end_activity">end_activity()</a>, <a href="#method_ba_MultiTeamSession__get_custom_menu_entries">get_custom_menu_entries()</a>, <a href="#method_ba_MultiTeamSession__get_ffa_series_length">get_ffa_series_length()</a>, <a href="#method_ba_MultiTeamSession__get_game_number">get_game_number()</a>, <a href="#method_ba_MultiTeamSession__get_max_players">get_max_players()</a>, <a href="#method_ba_MultiTeamSession__get_next_game_description">get_next_game_description()</a>, <a href="#method_ba_MultiTeamSession__get_series_length">get_series_length()</a>, <a href="#method_ba_MultiTeamSession__getactivity">getactivity()</a>, <a href="#method_ba_MultiTeamSession__handlemessage">handlemessage()</a>, <a href="#method_ba_MultiTeamSession__on_activity_end">on_activity_end()</a>, <a href="#method_ba_MultiTeamSession__on_player_leave">on_player_leave()</a>, <a href="#method_ba_MultiTeamSession__on_player_request">on_player_request()</a>, <a href="#method_ba_MultiTeamSession__on_team_join">on_team_join()</a>, <a href="#method_ba_MultiTeamSession__on_team_leave">on_team_leave()</a>, <a href="#method_ba_MultiTeamSession__setactivity">setactivity()</a>, <a href="#method_ba_MultiTeamSession__transitioning_out_activity_was_freed">transitioning_out_activity_was_freed()</a></h5>
<h3>Methods Defined or Overridden:</h3>
<h5><a href="#method_ba_FreeForAllSession____init__">&lt;constructor&gt;</a>, <a href="#method_ba_FreeForAllSession__get_ffa_point_awards">get_ffa_point_awards()</a></h5>
<dl>
<dt><h4><a name="method_ba_FreeForAllSession____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.FreeForAllSession()</span></p>

<p>Set up playlists and launches a <a href="#class_ba_Activity">ba.Activity</a> to accept joiners.</p>

</dd>
<dt><h4><a name="method_ba_FreeForAllSession__get_ffa_point_awards">get_ffa_point_awards()</a></dt></h4><dd>
<p><span>get_ffa_point_awards(self) -&gt; Dict[int, int]</span></p>

<p>Return the number of points awarded for different rankings.</p>

<p>This is based on the current number of players.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_FreezeMessage">ba.FreezeMessage</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Tells an object to become frozen.</p>

<p>Category: <a href="#class_category_Message_Classes">Message Classes</a></p>

<p>    As seen in the effects of an ice ba.Bomb.
</p>

<h3>Methods:</h3>
<dl>
<dt><h4><a name="method_ba_FreezeMessage____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.FreezeMessage()</span></p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_GameActivity">ba.GameActivity</a></strong></h3>
<p>Inherits from: <a href="#class_ba_Activity">ba.Activity</a>, <a href="#class_ba_DependencyComponent">ba.DependencyComponent</a>, <a href="https://docs.python.org/3/library/typing.html#typing.Generic">typing.Generic</a></p>
<p>Common base class for all game <a href="#class_ba_Activity">ba.Activities</a>.</p>

<p>Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a>
</p>

<h3>Attributes Inherited:</h3>
<h5><a href="#attr_ba_Activity__players">players</a>, <a href="#attr_ba_Activity__settings_raw">settings_raw</a>, <a href="#attr_ba_Activity__teams">teams</a></h5>
<h3>Attributes Defined Here:</h3>
<h5><a href="#attr_ba_GameActivity__customdata">customdata</a>, <a href="#attr_ba_GameActivity__expired">expired</a>, <a href="#attr_ba_GameActivity__globalsnode">globalsnode</a>, <a href="#attr_ba_GameActivity__map">map</a>, <a href="#attr_ba_GameActivity__playertype">playertype</a>, <a href="#attr_ba_GameActivity__session">session</a>, <a href="#attr_ba_GameActivity__stats">stats</a>, <a href="#attr_ba_GameActivity__teamtype">teamtype</a></h5>
<dl>
<dt><h4><a name="attr_ba_GameActivity__customdata">customdata</a></h4></dt><dd>
<p><span>dict</span></p>
<p>Entities needing to store simple data with an activity can put it
        here. This dict will be deleted when the activity expires, so contained
        objects generally do not need to worry about handling expired
        activities.</p>

</dd>
<dt><h4><a name="attr_ba_GameActivity__expired">expired</a></h4></dt><dd>
<p><span>bool</span></p>
<p>Whether the activity is expired.</p>

<p>        An activity is set as expired when shutting down.
        At this point no new nodes, timers, etc should be made,
        run, etc, and the activity should be considered a 'zombie'.</p>

</dd>
<dt><h4><a name="attr_ba_GameActivity__globalsnode">globalsnode</a></h4></dt><dd>
<p><span><a href="#class_ba_Node">ba.Node</a></span></p>
<p>The 'globals' <a href="#class_ba_Node">ba.Node</a> for the activity. This contains various
        global controls and values.</p>

</dd>
<dt><h4><a name="attr_ba_GameActivity__map">map</a></h4></dt><dd>
<p><span><a href="#class_ba_Map">ba.Map</a></span></p>
<p>The map being used for this game.</p>

<p>        Raises a <a href="#class_ba_NotFoundError">ba.NotFoundError</a> if the map does not currently exist.</p>

</dd>
<dt><h4><a name="attr_ba_GameActivity__playertype">playertype</a></h4></dt><dd>
<p><span>Type[PlayerType]</span></p>
<p>The type of <a href="#class_ba_Player">ba.Player</a> this Activity is using.</p>

</dd>
<dt><h4><a name="attr_ba_GameActivity__session">session</a></h4></dt><dd>
<p><span><a href="#class_ba_Session">ba.Session</a></span></p>
<p>The <a href="#class_ba_Session">ba.Session</a> this <a href="#class_ba_Activity">ba.Activity</a> belongs go.</p>

<p>        Raises a <a href="#class_ba_SessionNotFoundError">ba.SessionNotFoundError</a> if the Session no longer exists.</p>

</dd>
<dt><h4><a name="attr_ba_GameActivity__stats">stats</a></h4></dt><dd>
<p><span><a href="#class_ba_Stats">ba.Stats</a></span></p>
<p>The stats instance accessible while the activity is running.</p>

<p>        If access is attempted before or after, raises a <a href="#class_ba_NotFoundError">ba.NotFoundError</a>.</p>

</dd>
<dt><h4><a name="attr_ba_GameActivity__teamtype">teamtype</a></h4></dt><dd>
<p><span>Type[TeamType]</span></p>
<p>The type of <a href="#class_ba_Team">ba.Team</a> this Activity is using.</p>

</dd>
</dl>
<h3>Methods Inherited:</h3>
<h5><a href="#method_ba_Activity__add_actor_weak_ref">add_actor_weak_ref()</a>, <a href="#method_ba_Activity__add_player">add_player()</a>, <a href="#method_ba_Activity__add_team">add_team()</a>, <a href="#method_ba_Activity__begin">begin()</a>, <a href="#method_ba_Activity__create_player">create_player()</a>, <a href="#method_ba_Activity__create_team">create_team()</a>, <a href="#method_ba_Activity__dep_is_present">dep_is_present()</a>, <a href="#method_ba_Activity__expire">expire()</a>, <a href="#method_ba_Activity__get_dynamic_deps">get_dynamic_deps()</a>, <a href="#method_ba_Activity__has_begun">has_begun()</a>, <a href="#method_ba_Activity__has_ended">has_ended()</a>, <a href="#method_ba_Activity__has_transitioned_in">has_transitioned_in()</a>, <a href="#method_ba_Activity__is_transitioning_out">is_transitioning_out()</a>, <a href="#method_ba_Activity__on_expire">on_expire()</a>, <a href="#method_ba_Activity__on_player_leave">on_player_leave()</a>, <a href="#method_ba_Activity__on_team_join">on_team_join()</a>, <a href="#method_ba_Activity__on_team_leave">on_team_leave()</a>, <a href="#method_ba_Activity__on_transition_out">on_transition_out()</a>, <a href="#method_ba_Activity__remove_player">remove_player()</a>, <a href="#method_ba_Activity__remove_team">remove_team()</a>, <a href="#method_ba_Activity__retain_actor">retain_actor()</a>, <a href="#method_ba_Activity__set_has_ended">set_has_ended()</a>, <a href="#method_ba_Activity__transition_in">transition_in()</a>, <a href="#method_ba_Activity__transition_out">transition_out()</a></h5>
<h3>Methods Defined or Overridden:</h3>
<h5><a href="#method_ba_GameActivity____init__">&lt;constructor&gt;</a>, <a href="#method_ba_GameActivity__continue_or_end_game">continue_or_end_game()</a>, <a href="#method_ba_GameActivity__create_settings_ui">create_settings_ui()</a>, <a href="#method_ba_GameActivity__end">end()</a>, <a href="#method_ba_GameActivity__end_game">end_game()</a>, <a href="#method_ba_GameActivity__get_available_settings">get_available_settings()</a>, <a href="#method_ba_GameActivity__get_description">get_description()</a>, <a href="#method_ba_GameActivity__get_description_display_string">get_description_display_string()</a>, <a href="#method_ba_GameActivity__get_display_string">get_display_string()</a>, <a href="#method_ba_GameActivity__get_instance_description">get_instance_description()</a>, <a href="#method_ba_GameActivity__get_instance_description_short">get_instance_description_short()</a>, <a href="#method_ba_GameActivity__get_instance_display_string">get_instance_display_string()</a>, <a href="#method_ba_GameActivity__get_instance_scoreboard_display_string">get_instance_scoreboard_display_string()</a>, <a href="#method_ba_GameActivity__get_settings_display_string">get_settings_display_string()</a>, <a href="#method_ba_GameActivity__get_supported_maps">get_supported_maps()</a>, <a href="#method_ba_GameActivity__get_team_display_string">get_team_display_string()</a>, <a href="#method_ba_GameActivity__getname">getname()</a>, <a href="#method_ba_GameActivity__getscoreconfig">getscoreconfig()</a>, <a href="#method_ba_GameActivity__handlemessage">handlemessage()</a>, <a href="#method_ba_GameActivity__is_waiting_for_continue">is_waiting_for_continue()</a>, <a href="#method_ba_GameActivity__on_begin">on_begin()</a>, <a href="#method_ba_GameActivity__on_continue">on_continue()</a>, <a href="#method_ba_GameActivity__on_player_join">on_player_join()</a>, <a href="#method_ba_GameActivity__on_transition_in">on_transition_in()</a>, <a href="#method_ba_GameActivity__respawn_player">respawn_player()</a>, <a href="#method_ba_GameActivity__setup_standard_powerup_drops">setup_standard_powerup_drops()</a>, <a href="#method_ba_GameActivity__setup_standard_time_limit">setup_standard_time_limit()</a>, <a href="#method_ba_GameActivity__show_zoom_message">show_zoom_message()</a>, <a href="#method_ba_GameActivity__spawn_player">spawn_player()</a>, <a href="#method_ba_GameActivity__spawn_player_if_exists">spawn_player_if_exists()</a>, <a href="#method_ba_GameActivity__spawn_player_spaz">spawn_player_spaz()</a>, <a href="#method_ba_GameActivity__supports_session_type">supports_session_type()</a></h5>
<dl>
<dt><h4><a name="method_ba_GameActivity____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.GameActivity(settings: dict)</span></p>

<p>Instantiate the Activity.</p>

</dd>
<dt><h4><a name="method_ba_GameActivity__continue_or_end_game">continue_or_end_game()</a></dt></h4><dd>
<p><span>continue_or_end_game(self) -&gt; None</span></p>

<p>If continues are allowed, prompts the player to purchase a continue
and calls either end_game or continue_game depending on the result</p>

</dd>
<dt><h4><a name="method_ba_GameActivity__create_settings_ui">create_settings_ui()</a></dt></h4><dd>
<h5><span><em>&lt;class method&gt;</span></em></h5>
<p><span>create_settings_ui(sessiontype: Type[<a href="#class_ba_Session">ba.Session</a>], settings: Optional[dict], completion_call: Callable[[Optional[dict]], None]) -&gt; None </span></p>

<p>Launch an in-game UI to configure settings for a game type.</p>

<p>'sessiontype' should be the <a href="#class_ba_Session">ba.Session</a> class the game will be used in.</p>

<p>'settings' should be an existing settings dict (implies 'edit'
  ui mode) or None (implies 'add' ui mode).</p>

<p>'completion_call' will be called with a filled-out settings dict on
  success or None on cancel.</p>

<p>Generally subclasses don't need to override this; if they override
<a href="#method_ba_GameActivity__get_available_settings">ba.GameActivity.get_available_settings</a>() and
<a href="#method_ba_GameActivity__get_supported_maps">ba.GameActivity.get_supported_maps</a>() they can just rely on
the default implementation here which calls those methods.</p>

</dd>
<dt><h4><a name="method_ba_GameActivity__end">end()</a></dt></h4><dd>
<p><span>end(self, results: Any = None, delay: float = 0.0, force: bool = False) -&gt; None</span></p>

<p>Commences Activity shutdown and delivers results to the <a href="#class_ba_Session">ba.Session</a>.</p>

<p>'delay' is the time delay before the Activity actually ends
(in seconds). Further calls to end() will be ignored up until
this time, unless 'force' is True, in which case the new results
will replace the old.</p>

</dd>
<dt><h4><a name="method_ba_GameActivity__end_game">end_game()</a></dt></h4><dd>
<p><span>end_game(self) -&gt; None</span></p>

<p>Tell the game to wrap up and call <a href="#method_ba_Activity__end">ba.Activity.end</a>() immediately.</p>

<p>This method should be overridden by subclasses. A game should always
be prepared to end and deliver results, even if there is no 'winner'
yet; this way things like the standard time-limit
(<a href="#method_ba_GameActivity__setup_standard_time_limit">ba.GameActivity.setup_standard_time_limit</a>()) will work with the game.</p>

</dd>
<dt><h4><a name="method_ba_GameActivity__get_available_settings">get_available_settings()</a></dt></h4><dd>
<h5><span><em>&lt;class method&gt;</span></em></h5>
<p><span>get_available_settings(sessiontype: Type[<a href="#class_ba_Session">ba.Session</a>]) -&gt; List[<a href="#class_ba_Setting">ba.Setting</a>] </span></p>

<p>Return a list of settings relevant to this game type when
running under the provided session type.</p>

</dd>
<dt><h4><a name="method_ba_GameActivity__get_description">get_description()</a></dt></h4><dd>
<h5><span><em>&lt;class method&gt;</span></em></h5>
<p><span>get_description(sessiontype: Type[<a href="#class_ba_Session">ba.Session</a>]) -&gt; str </span></p>

<p>Get a str description of this game type.</p>

<p>The default implementation simply returns the 'description' class var.
Classes which want to change their description depending on the session
can override this method.</p>

</dd>
<dt><h4><a name="method_ba_GameActivity__get_description_display_string">get_description_display_string()</a></dt></h4><dd>
<h5><span><em>&lt;class method&gt;</span></em></h5>
<p><span>get_description_display_string(sessiontype: Type[<a href="#class_ba_Session">ba.Session</a>]) -&gt; <a href="#class_ba_Lstr">ba.Lstr</a> </span></p>

<p>Return a translated version of get_description().</p>

<p>Sub-classes should override get_description(); not this.</p>

</dd>
<dt><h4><a name="method_ba_GameActivity__get_display_string">get_display_string()</a></dt></h4><dd>
<h5><span><em>&lt;class method&gt;</span></em></h5>
<p><span>get_display_string(settings: Optional[Dict] = None) -&gt; <a href="#class_ba_Lstr">ba.Lstr</a> </span></p>

<p>Return a descriptive name for this game/settings combo.</p>

<p>Subclasses should override getname(); not this.</p>

</dd>
<dt><h4><a name="method_ba_GameActivity__get_instance_description">get_instance_description()</a></dt></h4><dd>
<p><span>get_instance_description(self) -&gt; Union[str, Sequence]</span></p>

<p>Return a description for this game instance, in English.</p>

<p>This is shown in the center of the screen below the game name at the
start of a game. It should start with a capital letter and end with a
period, and can be a bit more verbose than the version returned by
get_instance_description_short().</p>

<p>Note that translation is applied by looking up the specific returned
value as a key, so the number of returned variations should be limited;
ideally just one or two. To include arbitrary values in the
description, you can return a sequence of values in the following
form instead of just a string:</p>

<pre><span><em><small># This will give us something like 'Score 3 goals.' in English</small></em></span>
<span><em><small># and can properly translate to 'Anota 3 goles.' in Spanish.</small></em></span>
<span><em><small># If we just returned the string 'Score 3 Goals' here, there would</small></em></span>
<span><em><small># have to be a translation entry for each specific number. ew.</small></em></span>
return ['Score ${ARG1} goals.', self.settings_raw['Score to Win']]</pre>

<p>This way the first string can be consistently translated, with any arg
values then substituted into the result. ${ARG1} will be replaced with
the first value, ${ARG2} with the second, etc.</p>

</dd>
<dt><h4><a name="method_ba_GameActivity__get_instance_description_short">get_instance_description_short()</a></dt></h4><dd>
<p><span>get_instance_description_short(self) -&gt; Union[str, Sequence]</span></p>

<p>Return a short description for this game instance in English.</p>

<p>This description is used above the game scoreboard in the
corner of the screen, so it should be as concise as possible.
It should be lowercase and should not contain periods or other
punctuation.</p>

<p>Note that translation is applied by looking up the specific returned
value as a key, so the number of returned variations should be limited;
ideally just one or two. To include arbitrary values in the
description, you can return a sequence of values in the following form
instead of just a string:</p>

<pre><span><em><small># This will give us something like 'score 3 goals' in English</small></em></span>
<span><em><small># and can properly translate to 'anota 3 goles' in Spanish.</small></em></span>
<span><em><small># If we just returned the string 'score 3 goals' here, there would</small></em></span>
<span><em><small># have to be a translation entry for each specific number. ew.</small></em></span>
return ['score ${ARG1} goals', self.settings_raw['Score to Win']]</pre>

<p>This way the first string can be consistently translated, with any arg
values then substituted into the result. ${ARG1} will be replaced
with the first value, ${ARG2} with the second, etc.</p>

</dd>
<dt><h4><a name="method_ba_GameActivity__get_instance_display_string">get_instance_display_string()</a></dt></h4><dd>
<p><span>get_instance_display_string(self) -&gt; <a href="#class_ba_Lstr">ba.Lstr</a></span></p>

<p>Return a name for this particular game instance.</p>

</dd>
<dt><h4><a name="method_ba_GameActivity__get_instance_scoreboard_display_string">get_instance_scoreboard_display_string()</a></dt></h4><dd>
<p><span>get_instance_scoreboard_display_string(self) -&gt; <a href="#class_ba_Lstr">ba.Lstr</a></span></p>

<p>Return a name for this particular game instance.</p>

<p>This name is used above the game scoreboard in the corner
of the screen, so it should be as concise as possible.</p>

</dd>
<dt><h4><a name="method_ba_GameActivity__get_settings_display_string">get_settings_display_string()</a></dt></h4><dd>
<h5><span><em>&lt;class method&gt;</span></em></h5>
<p><span>get_settings_display_string(config: Dict[str, Any]) -&gt; <a href="#class_ba_Lstr">ba.Lstr</a> </span></p>

<p>Given a game config dict, return a short description for it.</p>

<p>This is used when viewing game-lists or showing what game
is up next in a series.</p>

</dd>
<dt><h4><a name="method_ba_GameActivity__get_supported_maps">get_supported_maps()</a></dt></h4><dd>
<h5><span><em>&lt;class method&gt;</span></em></h5>
<p><span>get_supported_maps(sessiontype: Type[<a href="#class_ba_Session">ba.Session</a>]) -&gt; List[str] </span></p>

<p>Called by the default <a href="#method_ba_GameActivity__create_settings_ui">ba.GameActivity.create_settings_ui</a>()
implementation; should return a list of map names valid
for this game-type for the given <a href="#class_ba_Session">ba.Session</a> type.</p>

</dd>
<dt><h4><a name="method_ba_GameActivity__get_team_display_string">get_team_display_string()</a></dt></h4><dd>
<h5><span><em>&lt;class method&gt;</span></em></h5>
<p><span>get_team_display_string(name: str) -&gt; <a href="#class_ba_Lstr">ba.Lstr</a> </span></p>

<p>Given a team name, returns a localized version of it.</p>

</dd>
<dt><h4><a name="method_ba_GameActivity__getname">getname()</a></dt></h4><dd>
<h5><span><em>&lt;class method&gt;</span></em></h5>
<p><span>getname() -&gt; str </span></p>

<p>Return a str name for this game type.</p>

<p>This default implementation simply returns the 'name' class attr.</p>

</dd>
<dt><h4><a name="method_ba_GameActivity__getscoreconfig">getscoreconfig()</a></dt></h4><dd>
<h5><span><em>&lt;class method&gt;</span></em></h5>
<p><span>getscoreconfig() -&gt; <a href="#class_ba_ScoreConfig">ba.ScoreConfig</a> </span></p>

<p>Return info about game scoring setup; can be overridden by games.</p>

</dd>
<dt><h4><a name="method_ba_GameActivity__handlemessage">handlemessage()</a></dt></h4><dd>
<p><span>handlemessage(self, msg: Any) -&gt; Any</span></p>

<p>General message handling; can be passed any <a href="#class_category_Message_Classes">message object</a>.</p>

</dd>
<dt><h4><a name="method_ba_GameActivity__is_waiting_for_continue">is_waiting_for_continue()</a></dt></h4><dd>
<p><span>is_waiting_for_continue(self) -&gt; bool</span></p>

<p>Returns whether or not this activity is currently waiting for the
player to continue (or timeout)</p>

</dd>
<dt><h4><a name="method_ba_GameActivity__on_begin">on_begin()</a></dt></h4><dd>
<p><span>on_begin(self) -&gt; None</span></p>

<p>Called once the previous <a href="#class_ba_Activity">ba.Activity</a> has finished transitioning out.</p>

<p>At this point the activity's initial players and teams are filled in
and it should begin its actual game logic.</p>

</dd>
<dt><h4><a name="method_ba_GameActivity__on_continue">on_continue()</a></dt></h4><dd>
<p><span>on_continue(self) -&gt; None</span></p>

<p>This is called if a game supports and offers a continue and the player
accepts.  In this case the player should be given an extra life or
whatever is relevant to keep the game going.</p>

</dd>
<dt><h4><a name="method_ba_GameActivity__on_player_join">on_player_join()</a></dt></h4><dd>
<p><span>on_player_join(self, player: PlayerType) -&gt; None</span></p>

<p>Called when a new <a href="#class_ba_Player">ba.Player</a> has joined the Activity.</p>

<p>(including the initial set of Players)</p>

</dd>
<dt><h4><a name="method_ba_GameActivity__on_transition_in">on_transition_in()</a></dt></h4><dd>
<p><span>on_transition_in(self) -&gt; None</span></p>

<p>Called when the Activity is first becoming visible.</p>

<p>Upon this call, the Activity should fade in backgrounds,
start playing music, etc. It does not yet have access to players
or teams, however. They remain owned by the previous Activity
up until <a href="#method_ba_Activity__on_begin">ba.Activity.on_begin</a>() is called.</p>

</dd>
<dt><h4><a name="method_ba_GameActivity__respawn_player">respawn_player()</a></dt></h4><dd>
<p><span>respawn_player(self, player: PlayerType, respawn_time: Optional[float] = None) -&gt; None</span></p>

<p>Given a <a href="#class_ba_Player">ba.Player</a>, sets up a standard respawn timer,
along with the standard counter display, etc.
At the end of the respawn period spawn_player() will
be called if the Player still exists.
An explicit 'respawn_time' can optionally be provided
(in seconds).</p>

</dd>
<dt><h4><a name="method_ba_GameActivity__setup_standard_powerup_drops">setup_standard_powerup_drops()</a></dt></h4><dd>
<p><span>setup_standard_powerup_drops(self, enable_tnt: bool = True) -&gt; None</span></p>

<p>Create standard powerup drops for the current map.</p>

</dd>
<dt><h4><a name="method_ba_GameActivity__setup_standard_time_limit">setup_standard_time_limit()</a></dt></h4><dd>
<p><span>setup_standard_time_limit(self, duration: float) -&gt; None</span></p>

<p>Create a standard game time-limit given the provided
duration in seconds.
This will be displayed at the top of the screen.
If the time-limit expires, end_game() will be called.</p>

</dd>
<dt><h4><a name="method_ba_GameActivity__show_zoom_message">show_zoom_message()</a></dt></h4><dd>
<p><span>show_zoom_message(self, message: <a href="#class_ba_Lstr">ba.Lstr</a>, color: Sequence[float] = (0.9, 0.4, 0.0), scale: float = 0.8, duration: float = 2.0, trail: bool = False) -&gt; None</span></p>

<p>Zooming text used to announce game names and winners.</p>

</dd>
<dt><h4><a name="method_ba_GameActivity__spawn_player">spawn_player()</a></dt></h4><dd>
<p><span>spawn_player(self, player: PlayerType) -&gt; <a href="#class_ba_Actor">ba.Actor</a></span></p>

<p>Spawn *something* for the provided <a href="#class_ba_Player">ba.Player</a>.</p>

<p>The default implementation simply calls spawn_player_spaz().</p>

</dd>
<dt><h4><a name="method_ba_GameActivity__spawn_player_if_exists">spawn_player_if_exists()</a></dt></h4><dd>
<p><span>spawn_player_if_exists(self, player: PlayerType) -&gt; None</span></p>

<p>A utility method which calls self.spawn_player() *only* if the
<a href="#class_ba_Player">ba.Player</a> provided still exists; handy for use in timers and whatnot.</p>

<p>There is no need to override this; just override spawn_player().</p>

</dd>
<dt><h4><a name="method_ba_GameActivity__spawn_player_spaz">spawn_player_spaz()</a></dt></h4><dd>
<p><span>spawn_player_spaz(self, player: PlayerType, position: Sequence[float] = (0, 0, 0), angle: float = None) -&gt; PlayerSpaz</span></p>

<p>Create and wire up a ba.PlayerSpaz for the provided <a href="#class_ba_Player">ba.Player</a>.</p>

</dd>
<dt><h4><a name="method_ba_GameActivity__supports_session_type">supports_session_type()</a></dt></h4><dd>
<h5><span><em>&lt;class method&gt;</span></em></h5>
<p><span>supports_session_type(sessiontype: Type[<a href="#class_ba_Session">ba.Session</a>]) -&gt; bool </span></p>

<p>Return whether this game supports the provided Session type.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_GameResults">ba.GameResults</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>
Results for a completed game.</p>

<p>Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a></p>

<p>Upon completion, a game should fill one of these out and pass it to its
<a href="#method_ba_Activity__end">ba.Activity.end</a>() call.</p>

<h3>Attributes:</h3>
<h5><a href="#attr_ba_GameResults__lower_is_better">lower_is_better</a>, <a href="#attr_ba_GameResults__playerinfos">playerinfos</a>, <a href="#attr_ba_GameResults__score_label">score_label</a>, <a href="#attr_ba_GameResults__scoretype">scoretype</a>, <a href="#attr_ba_GameResults__sessionteams">sessionteams</a>, <a href="#attr_ba_GameResults__winnergroups">winnergroups</a>, <a href="#attr_ba_GameResults__winning_sessionteam">winning_sessionteam</a></h5>
<dl>
<dt><h4><a name="attr_ba_GameResults__lower_is_better">lower_is_better</a></h4></dt><dd>
<p><span>bool</span></p>
<p>Whether lower scores are better.</p>

</dd>
<dt><h4><a name="attr_ba_GameResults__playerinfos">playerinfos</a></h4></dt><dd>
<p><span>List[<a href="#class_ba_PlayerInfo">ba.PlayerInfo</a>]</span></p>
<p>Get info about the players represented by the results.</p>

</dd>
<dt><h4><a name="attr_ba_GameResults__score_label">score_label</a></h4></dt><dd>
<p><span>str</span></p>
<p>The label associated with scores ('points', etc).</p>

</dd>
<dt><h4><a name="attr_ba_GameResults__scoretype">scoretype</a></h4></dt><dd>
<p><span><a href="#class_ba_ScoreType">ba.ScoreType</a></span></p>
<p>The type of score.</p>

</dd>
<dt><h4><a name="attr_ba_GameResults__sessionteams">sessionteams</a></h4></dt><dd>
<p><span>List[<a href="#class_ba_SessionTeam">ba.SessionTeam</a>]</span></p>
<p>Return all <a href="#class_ba_SessionTeam">ba.SessionTeams</a> in the results.</p>

</dd>
<dt><h4><a name="attr_ba_GameResults__winnergroups">winnergroups</a></h4></dt><dd>
<p><span>List[WinnerGroup]</span></p>
<p>Get an ordered list of winner groups.</p>

</dd>
<dt><h4><a name="attr_ba_GameResults__winning_sessionteam">winning_sessionteam</a></h4></dt><dd>
<p><span>Optional[<a href="#class_ba_SessionTeam">ba.SessionTeam</a>]</span></p>
<p>The winning <a href="#class_ba_SessionTeam">ba.SessionTeam</a> if there is exactly one, or else None.</p>

</dd>
</dl>
<h3>Methods:</h3>
<h5><a href="#method_ba_GameResults____init__">&lt;constructor&gt;</a>, <a href="#method_ba_GameResults__get_sessionteam_score">get_sessionteam_score()</a>, <a href="#method_ba_GameResults__get_sessionteam_score_str">get_sessionteam_score_str()</a>, <a href="#method_ba_GameResults__has_score_for_sessionteam">has_score_for_sessionteam()</a>, <a href="#method_ba_GameResults__set_game">set_game()</a>, <a href="#method_ba_GameResults__set_team_score">set_team_score()</a></h5>
<dl>
<dt><h4><a name="method_ba_GameResults____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.GameResults()</span></p>

</dd>
<dt><h4><a name="method_ba_GameResults__get_sessionteam_score">get_sessionteam_score()</a></dt></h4><dd>
<p><span>get_sessionteam_score(self, sessionteam: <a href="#class_ba_SessionTeam">ba.SessionTeam</a>) -&gt; Optional[int]</span></p>

<p>Return the score for a given <a href="#class_ba_SessionTeam">ba.SessionTeam</a>.</p>

</dd>
<dt><h4><a name="method_ba_GameResults__get_sessionteam_score_str">get_sessionteam_score_str()</a></dt></h4><dd>
<p><span>get_sessionteam_score_str(self, sessionteam: <a href="#class_ba_SessionTeam">ba.SessionTeam</a>) -&gt; <a href="#class_ba_Lstr">ba.Lstr</a></span></p>

<p>Return the score for the given session-team as an Lstr.</p>

<p>(properly formatted for the score type.)</p>

</dd>
<dt><h4><a name="method_ba_GameResults__has_score_for_sessionteam">has_score_for_sessionteam()</a></dt></h4><dd>
<p><span>has_score_for_sessionteam(self, sessionteam: <a href="#class_ba_SessionTeam">ba.SessionTeam</a>) -&gt; bool</span></p>

<p>Return whether there is a score for a given session-team.</p>

</dd>
<dt><h4><a name="method_ba_GameResults__set_game">set_game()</a></dt></h4><dd>
<p><span>set_game(self, game: <a href="#class_ba_GameActivity">ba.GameActivity</a>) -&gt; None</span></p>

<p>Set the game instance these results are applying to.</p>

</dd>
<dt><h4><a name="method_ba_GameResults__set_team_score">set_team_score()</a></dt></h4><dd>
<p><span>set_team_score(self, team: <a href="#class_ba_Team">ba.Team</a>, score: Optional[int]) -&gt; None</span></p>

<p>Set the score for a given team.</p>

<p>This can be a number or None.
(see the none_is_winner arg in the constructor)</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_GameTip">ba.GameTip</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Defines a tip presentable to the user at the start of a game.</p>

<p>Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a>
</p>

<h3>Methods:</h3>
<dl>
<dt><h4><a name="method_ba_GameTip____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.GameTip(text: str, icon: Optional[<a href="#class_ba_Texture">ba.Texture</a>] = None, sound: Optional[<a href="#class_ba_Sound">ba.Sound</a>] = None)</span></p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_HitMessage">ba.HitMessage</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Tells an object it has been hit in some way.</p>

<p>Category: <a href="#class_category_Message_Classes">Message Classes</a></p>

<p>    This is used by punches, explosions, etc to convey
    their effect to a target.
</p>

<h3>Methods:</h3>
<h5><a href="#method_ba_HitMessage____init__">&lt;constructor&gt;</a>, <a href="#method_ba_HitMessage__get_source_player">get_source_player()</a></h5>
<dl>
<dt><h4><a name="method_ba_HitMessage____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.HitMessage(srcnode: '<a href="#class_ba_Node">ba.Node</a>' = None, pos: 'Sequence[float]' = None, velocity: 'Sequence[float]' = None, magnitude: 'float' = 1.0, velocity_magnitude: 'float' = 0.0, radius: 'float' = 1.0, source_player: '<a href="#class_ba_Player">ba.Player</a>' = None, kick_back: 'float' = 1.0, flat_damage: 'float' = None, hit_type: 'str' = 'generic', force_direction: 'Sequence[float]' = None, hit_subtype: 'str' = 'default')</span></p>

<p>Instantiate a message with given values.</p>

</dd>
<dt><h4><a name="method_ba_HitMessage__get_source_player">get_source_player()</a></dt></h4><dd>
<p><span>get_source_player(self, playertype: Type[PlayerType]) -&gt; Optional[PlayerType]</span></p>

<p>Return the source-player if one exists and is the provided type.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_ImpactDamageMessage">ba.ImpactDamageMessage</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Tells an object that it has been jarred violently.</p>

<p>Category: <a href="#class_category_Message_Classes">Message Classes</a></p>

<h3>Attributes:</h3>
<dl>
<dt><h4><a name="attr_ba_ImpactDamageMessage__intensity">intensity</a></h4></dt><dd>
<p><span>float</span></p>
<p>The intensity of the impact.</p>

</dd>
</dl>
<h3>Methods:</h3>
<dl>
<dt><h4><a name="method_ba_ImpactDamageMessage____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.ImpactDamageMessage(intensity: float)</span></p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_InputDevice">ba.InputDevice</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>An input-device such as a gamepad, touchscreen, or keyboard.</p>

<p>Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a></p>

<h3>Attributes:</h3>
<h5><a href="#attr_ba_InputDevice__allows_configuring">allows_configuring</a>, <a href="#attr_ba_InputDevice__client_id">client_id</a>, <a href="#attr_ba_InputDevice__has_meaningful_button_names">has_meaningful_button_names</a>, <a href="#attr_ba_InputDevice__id">id</a>, <a href="#attr_ba_InputDevice__instance_number">instance_number</a>, <a href="#attr_ba_InputDevice__is_controller_app">is_controller_app</a>, <a href="#attr_ba_InputDevice__is_remote_client">is_remote_client</a>, <a href="#attr_ba_InputDevice__name">name</a>, <a href="#attr_ba_InputDevice__player">player</a>, <a href="#attr_ba_InputDevice__unique_identifier">unique_identifier</a></h5>
<dl>
<dt><h4><a name="attr_ba_InputDevice__allows_configuring">allows_configuring</a></h4></dt><dd>
<p><span> bool</span></p>
<p>Whether the input-device can be configured.</p>

</dd>
<dt><h4><a name="attr_ba_InputDevice__client_id">client_id</a></h4></dt><dd>
<p><span> int</span></p>
<p>The numeric client-id this device is associated with.
This is only meaningful for remote client inputs; for
all local devices this will be -1.</p>

</dd>
<dt><h4><a name="attr_ba_InputDevice__has_meaningful_button_names">has_meaningful_button_names</a></h4></dt><dd>
<p><span> bool</span></p>
<p>Whether button names returned by this instance match labels
on the actual device. (Can be used to determine whether to show
them in controls-overlays, etc.)</p>

</dd>
<dt><h4><a name="attr_ba_InputDevice__id">id</a></h4></dt><dd>
<p><span> int</span></p>
<p>The unique numeric id of this device.</p>

</dd>
<dt><h4><a name="attr_ba_InputDevice__instance_number">instance_number</a></h4></dt><dd>
<p><span> int</span></p>
<p>The number of this device among devices of the same type.</p>

</dd>
<dt><h4><a name="attr_ba_InputDevice__is_controller_app">is_controller_app</a></h4></dt><dd>
<p><span> bool</span></p>
<p>Whether this input-device represents a locally-connected
controller-app.</p>

</dd>
<dt><h4><a name="attr_ba_InputDevice__is_remote_client">is_remote_client</a></h4></dt><dd>
<p><span> bool</span></p>
<p>Whether this input-device represents a remotely-connected
client.</p>

</dd>
<dt><h4><a name="attr_ba_InputDevice__name">name</a></h4></dt><dd>
<p><span> str</span></p>
<p>The name of the device.</p>

</dd>
<dt><h4><a name="attr_ba_InputDevice__player">player</a></h4></dt><dd>
<p><span> Optional[<a href="#class_ba_SessionPlayer">ba.SessionPlayer</a>]</span></p>
<p>The player associated with this input device.</p>

</dd>
<dt><h4><a name="attr_ba_InputDevice__unique_identifier">unique_identifier</a></h4></dt><dd>
<p><span> str</span></p>
<p>A string that can be used to persistently identify the device,
even among other devices of the same type. Used for saving
prefs, etc.</p>

</dd>
</dl>
<h3>Methods:</h3>
<h5><a href="#method_ba_InputDevice__exists">exists()</a>, <a href="#method_ba_InputDevice__get_account_name">get_account_name()</a>, <a href="#method_ba_InputDevice__get_axis_name">get_axis_name()</a>, <a href="#method_ba_InputDevice__get_button_name">get_button_name()</a></h5>
<dl>
<dt><h4><a name="method_ba_InputDevice__exists">exists()</a></dt></h4><dd>
<p><span>exists() -&gt; bool</span></p>

<p>Return whether the underlying device for this object is still present.</p>

</dd>
<dt><h4><a name="method_ba_InputDevice__get_account_name">get_account_name()</a></dt></h4><dd>
<p><span>get_account_name(full: bool) -&gt; str</span></p>

<p>Returns the account name associated with this device.</p>

<p>(can be used to get account names for remote players)</p>

</dd>
<dt><h4><a name="method_ba_InputDevice__get_axis_name">get_axis_name()</a></dt></h4><dd>
<p><span>get_axis_name(axis_id: int) -&gt; str</span></p>

<p>Given an axis ID, return the name of the axis on this device.</p>

<p>Can return an empty string if the value is not meaningful to humans.</p>

</dd>
<dt><h4><a name="method_ba_InputDevice__get_button_name">get_button_name()</a></dt></h4><dd>
<p><span>get_button_name(button_id: int) -&gt; <a href="#class_ba_Lstr">ba.Lstr</a></span></p>

<p>Given a button ID, return a human-readable name for that key/button.</p>

<p>Can return an empty string if the value is not meaningful to humans.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_InputDeviceNotFoundError">ba.InputDeviceNotFoundError</a></strong></h3>
<p>Inherits from: <a href="#class_ba_NotFoundError">ba.NotFoundError</a>, <a href="https://docs.python.org/3/library/exceptions.html#Exception">Exception</a>, <a href="https://docs.python.org/3/library/exceptions.html#BaseException">BaseException</a></p>
<p>Exception raised when an expected <a href="#class_ba_InputDevice">ba.InputDevice</a> does not exist.</p>

<p>Category: <a href="#class_category_Exception_Classes">Exception Classes</a>
</p>

<h3>Methods:</h3>
<p>&lt;all methods inherited from <a href="#class_ba_NotFoundError">ba.NotFoundError</a>&gt;</p>
<hr>
<h2><strong><a name="class_ba_InputType">ba.InputType</a></strong></h3>
<p>Inherits from: <a href="https://docs.python.org/3/library/enum.html#enum.Enum">enum.Enum</a></p>
<p>Types of input a controller can send to the game.</p>

<p>Category: <a href="#class_category_Enums">Enums</a></p>

<p></p>

<h3>Values:</h3>
<ul>
<li>UP_DOWN</li>
<li>LEFT_RIGHT</li>
<li>JUMP_PRESS</li>
<li>JUMP_RELEASE</li>
<li>PUNCH_PRESS</li>
<li>PUNCH_RELEASE</li>
<li>BOMB_PRESS</li>
<li>BOMB_RELEASE</li>
<li>PICK_UP_PRESS</li>
<li>PICK_UP_RELEASE</li>
<li>RUN</li>
<li>FLY_PRESS</li>
<li>FLY_RELEASE</li>
<li>START_PRESS</li>
<li>START_RELEASE</li>
<li>HOLD_POSITION_PRESS</li>
<li>HOLD_POSITION_RELEASE</li>
<li>LEFT_PRESS</li>
<li>LEFT_RELEASE</li>
<li>RIGHT_PRESS</li>
<li>RIGHT_RELEASE</li>
<li>UP_PRESS</li>
<li>UP_RELEASE</li>
<li>DOWN_PRESS</li>
<li>DOWN_RELEASE</li>
</ul>
<hr>
<h2><strong><a name="class_ba_IntChoiceSetting">ba.IntChoiceSetting</a></strong></h3>
<p>Inherits from: <a href="#class_ba_ChoiceSetting">ba.ChoiceSetting</a>, <a href="#class_ba_Setting">ba.Setting</a></p>
<p>An int setting with multiple choices.</p>

<p>Category: <a href="#class_category_Settings_Classes">Settings Classes</a>
</p>

<h3>Methods:</h3>
<dl>
<dt><h4><a name="method_ba_IntChoiceSetting____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.IntChoiceSetting(name: str, default: int, choices: List[Tuple[str, int]])</span></p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_IntSetting">ba.IntSetting</a></strong></h3>
<p>Inherits from: <a href="#class_ba_Setting">ba.Setting</a></p>
<p>An integer game setting.</p>

<p>Category: <a href="#class_category_Settings_Classes">Settings Classes</a>
</p>

<h3>Methods:</h3>
<dl>
<dt><h4><a name="method_ba_IntSetting____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.IntSetting(name: str, default: int, min_value: int = 0, max_value: int = 9999, increment: int = 1)</span></p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_Keyboard">ba.Keyboard</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Chars definitions for on-screen keyboard.</p>

<p>Category: <a href="#class_category_App_Classes">App Classes</a></p>

<p>    Keyboards are discoverable by the meta-tag system
    and the user can select which one they want to use.
    On-screen keyboard uses chars from active <a href="#class_ba_Keyboard">ba.Keyboard</a>.</p>

<h3>Attributes:</h3>
<h5><a href="#attr_ba_Keyboard__chars">chars</a>, <a href="#attr_ba_Keyboard__name">name</a>, <a href="#attr_ba_Keyboard__nums">nums</a>, <a href="#attr_ba_Keyboard__pages">pages</a></h5>
<dl>
<dt><h4><a name="attr_ba_Keyboard__chars">chars</a></h4></dt><dd>
<p><span>List[Tuple[str, ...]]</span></p>
<p>Used for row/column lengths.</p>

</dd>
<dt><h4><a name="attr_ba_Keyboard__name">name</a></h4></dt><dd>
<p><span>str</span></p>
<p>Displays when user selecting this keyboard.</p>

</dd>
<dt><h4><a name="attr_ba_Keyboard__nums">nums</a></h4></dt><dd>
<p><span>Tuple[str, ...]</span></p>
<p>The 'num' page.</p>

</dd>
<dt><h4><a name="attr_ba_Keyboard__pages">pages</a></h4></dt><dd>
<p><span>Dict[str, Tuple[str, ...]]</span></p>
<p>Extra chars like emojis.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_LanguageSubsystem">ba.LanguageSubsystem</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Wraps up language related app functionality.</p>

<p>Category: <a href="#class_category_App_Classes">App Classes</a></p>

<p>    To use this class, access the single instance of it at 'ba.app.lang'.
</p>

<h3>Attributes:</h3>
<h5><a href="#attr_ba_LanguageSubsystem__available_languages">available_languages</a>, <a href="#attr_ba_LanguageSubsystem__language">language</a>, <a href="#attr_ba_LanguageSubsystem__locale">locale</a></h5>
<dl>
<dt><h4><a name="attr_ba_LanguageSubsystem__available_languages">available_languages</a></h4></dt><dd>
<p><span>List[str]</span></p>
<p>A list of all available languages.</p>

<p>        Note that languages that may be present in game assets but which
        are not displayable on the running version of the game are not
        included here.</p>

</dd>
<dt><h4><a name="attr_ba_LanguageSubsystem__language">language</a></h4></dt><dd>
<p><span>str</span></p>
<p>The name of the language the game is running in.</p>

<p>        This can be selected explicitly by the user or may be set
        automatically based on <a href="#class_ba_App">ba.App</a>.locale or other factors.</p>

</dd>
<dt><h4><a name="attr_ba_LanguageSubsystem__locale">locale</a></h4></dt><dd>
<p><span>str</span></p>
<p>Raw country/language code detected by the game (such as 'en_US').</p>

<p>        Generally for language-specific code you should look at
        <a href="#class_ba_App">ba.App</a>.language, which is the language the game is using
        (which may differ from locale if the user sets a language, etc.)</p>

</dd>
</dl>
<h3>Methods:</h3>
<h5><a href="#method_ba_LanguageSubsystem____init__">&lt;constructor&gt;</a>, <a href="#method_ba_LanguageSubsystem__get_resource">get_resource()</a>, <a href="#method_ba_LanguageSubsystem__is_custom_unicode_char">is_custom_unicode_char()</a>, <a href="#method_ba_LanguageSubsystem__setlanguage">setlanguage()</a>, <a href="#method_ba_LanguageSubsystem__translate">translate()</a></h5>
<dl>
<dt><h4><a name="method_ba_LanguageSubsystem____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.LanguageSubsystem()</span></p>

</dd>
<dt><h4><a name="method_ba_LanguageSubsystem__get_resource">get_resource()</a></dt></h4><dd>
<p><span>get_resource(self, resource: str, fallback_resource: str = None, fallback_value: Any = None) -&gt; Any</span></p>

<p>Return a translation resource by name.</p>

<p>DEPRECATED; use <a href="#class_ba_Lstr">ba.Lstr</a> functionality for these purposes.</p>

</dd>
<dt><h4><a name="method_ba_LanguageSubsystem__is_custom_unicode_char">is_custom_unicode_char()</a></dt></h4><dd>
<p><span>is_custom_unicode_char(self, char: str) -&gt; bool</span></p>

<p>Return whether a char is in the custom unicode range we use.</p>

</dd>
<dt><h4><a name="method_ba_LanguageSubsystem__setlanguage">setlanguage()</a></dt></h4><dd>
<p><span>setlanguage(self, language: Optional[str], print_change: bool = True, store_to_config: bool = True) -&gt; None</span></p>

<p>Set the active language used for the game.</p>

<p>Pass None to use OS default language.</p>

</dd>
<dt><h4><a name="method_ba_LanguageSubsystem__translate">translate()</a></dt></h4><dd>
<p><span>translate(self, category: str, strval: str, raise_exceptions: bool = False, print_errors: bool = False) -&gt; str</span></p>

<p>Translate a value (or return the value if no translation available)</p>

<p>DEPRECATED; use <a href="#class_ba_Lstr">ba.Lstr</a> functionality for these purposes.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_Level">ba.Level</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>An entry in a <a href="#class_ba_Campaign">ba.Campaign</a> consisting of a name, game type, and settings.</p>

<p>Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a>
</p>

<h3>Attributes:</h3>
<h5><a href="#attr_ba_Level__campaign">campaign</a>, <a href="#attr_ba_Level__complete">complete</a>, <a href="#attr_ba_Level__displayname">displayname</a>, <a href="#attr_ba_Level__gametype">gametype</a>, <a href="#attr_ba_Level__index">index</a>, <a href="#attr_ba_Level__name">name</a>, <a href="#attr_ba_Level__preview_texture_name">preview_texture_name</a>, <a href="#attr_ba_Level__rating">rating</a></h5>
<dl>
<dt><h4><a name="attr_ba_Level__campaign">campaign</a></h4></dt><dd>
<p><span>Optional[<a href="#class_ba_Campaign">ba.Campaign</a>]</span></p>
<p>The <a href="#class_ba_Campaign">ba.Campaign</a> this Level is associated with, or None.</p>

</dd>
<dt><h4><a name="attr_ba_Level__complete">complete</a></h4></dt><dd>
<p><span>bool</span></p>
<p>Whether this Level has been completed.</p>

</dd>
<dt><h4><a name="attr_ba_Level__displayname">displayname</a></h4></dt><dd>
<p><span><a href="#class_ba_Lstr">ba.Lstr</a></span></p>
<p>The localized name for this Level.</p>

</dd>
<dt><h4><a name="attr_ba_Level__gametype">gametype</a></h4></dt><dd>
<p><span>Type[<a href="#class_ba_GameActivity">ba.GameActivity</a>]</span></p>
<p>The type of game used for this Level.</p>

</dd>
<dt><h4><a name="attr_ba_Level__index">index</a></h4></dt><dd>
<p><span>int</span></p>
<p>The zero-based index of this Level in its <a href="#class_ba_Campaign">ba.Campaign</a>.</p>

<p>        Access results in a RuntimeError if the Level is  not assigned to a
        Campaign.</p>

</dd>
<dt><h4><a name="attr_ba_Level__name">name</a></h4></dt><dd>
<p><span>str</span></p>
<p>The unique name for this Level.</p>

</dd>
<dt><h4><a name="attr_ba_Level__preview_texture_name">preview_texture_name</a></h4></dt><dd>
<p><span>str</span></p>
<p>The preview texture name for this Level.</p>

</dd>
<dt><h4><a name="attr_ba_Level__rating">rating</a></h4></dt><dd>
<p><span>float</span></p>
<p>The current rating for this Level.</p>

</dd>
</dl>
<h3>Methods:</h3>
<h5><a href="#method_ba_Level____init__">&lt;constructor&gt;</a>, <a href="#method_ba_Level__get_high_scores">get_high_scores()</a>, <a href="#method_ba_Level__get_preview_texture">get_preview_texture()</a>, <a href="#method_ba_Level__get_score_version_string">get_score_version_string()</a>, <a href="#method_ba_Level__get_settings">get_settings()</a>, <a href="#method_ba_Level__set_complete">set_complete()</a>, <a href="#method_ba_Level__set_high_scores">set_high_scores()</a>, <a href="#method_ba_Level__set_rating">set_rating()</a></h5>
<dl>
<dt><h4><a name="method_ba_Level____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.Level(name: str, gametype: Type[<a href="#class_ba_GameActivity">ba.GameActivity</a>], settings: dict, preview_texture_name: str, displayname: str = None)</span></p>

</dd>
<dt><h4><a name="method_ba_Level__get_high_scores">get_high_scores()</a></dt></h4><dd>
<p><span>get_high_scores(self) -&gt; dict</span></p>

<p>Return the current high scores for this Level.</p>

</dd>
<dt><h4><a name="method_ba_Level__get_preview_texture">get_preview_texture()</a></dt></h4><dd>
<p><span>get_preview_texture(self) -&gt; <a href="#class_ba_Texture">ba.Texture</a></span></p>

<p>Load/return the preview Texture for this Level.</p>

</dd>
<dt><h4><a name="method_ba_Level__get_score_version_string">get_score_version_string()</a></dt></h4><dd>
<p><span>get_score_version_string(self) -&gt; str</span></p>

<p>Return the score version string for this Level.</p>

<p>If a Level's gameplay changes significantly, its version string
can be changed to separate its new high score lists/etc. from the old.</p>

</dd>
<dt><h4><a name="method_ba_Level__get_settings">get_settings()</a></dt></h4><dd>
<p><span>get_settings(self) -&gt; Dict[str, Any]</span></p>

<p>Returns the settings for this Level.</p>

</dd>
<dt><h4><a name="method_ba_Level__set_complete">set_complete()</a></dt></h4><dd>
<p><span>set_complete(self, val: bool) -&gt; None</span></p>

<p>Set whether or not this level is complete.</p>

</dd>
<dt><h4><a name="method_ba_Level__set_high_scores">set_high_scores()</a></dt></h4><dd>
<p><span>set_high_scores(self, high_scores: Dict) -&gt; None</span></p>

<p>Set high scores for this level.</p>

</dd>
<dt><h4><a name="method_ba_Level__set_rating">set_rating()</a></dt></h4><dd>
<p><span>set_rating(self, rating: float) -&gt; None</span></p>

<p>Set a rating for this Level, replacing the old ONLY IF higher.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_Lobby">ba.Lobby</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Container for <a href="#class_ba_Chooser">ba.Choosers</a>.</p>

<p>Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a>
</p>

<h3>Attributes:</h3>
<h5><a href="#attr_ba_Lobby__sessionteams">sessionteams</a>, <a href="#attr_ba_Lobby__use_team_colors">use_team_colors</a></h5>
<dl>
<dt><h4><a name="attr_ba_Lobby__sessionteams">sessionteams</a></h4></dt><dd>
<p><span>List[<a href="#class_ba_SessionTeam">ba.SessionTeam</a>]</span></p>
<p><a href="#class_ba_SessionTeam">ba.SessionTeams</a> available in this lobby.</p>

</dd>
<dt><h4><a name="attr_ba_Lobby__use_team_colors">use_team_colors</a></h4></dt><dd>
<p><span>bool</span></p>
<p>A bool for whether this lobby is using team colors.</p>

<p>        If False, inidividual player colors are used instead.</p>

</dd>
</dl>
<h3>Methods:</h3>
<h5><a href="#method_ba_Lobby____init__">&lt;constructor&gt;</a>, <a href="#method_ba_Lobby__add_chooser">add_chooser()</a>, <a href="#method_ba_Lobby__check_all_ready">check_all_ready()</a>, <a href="#method_ba_Lobby__create_join_info">create_join_info()</a>, <a href="#method_ba_Lobby__get_choosers">get_choosers()</a>, <a href="#method_ba_Lobby__reload_profiles">reload_profiles()</a>, <a href="#method_ba_Lobby__remove_all_choosers">remove_all_choosers()</a>, <a href="#method_ba_Lobby__remove_all_choosers_and_kick_players">remove_all_choosers_and_kick_players()</a>, <a href="#method_ba_Lobby__remove_chooser">remove_chooser()</a>, <a href="#method_ba_Lobby__update_positions">update_positions()</a></h5>
<dl>
<dt><h4><a name="method_ba_Lobby____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.Lobby()</span></p>

</dd>
<dt><h4><a name="method_ba_Lobby__add_chooser">add_chooser()</a></dt></h4><dd>
<p><span>add_chooser(self, sessionplayer: <a href="#class_ba_SessionPlayer">ba.SessionPlayer</a>) -&gt; None</span></p>

<p>Add a chooser to the lobby for the provided player.</p>

</dd>
<dt><h4><a name="method_ba_Lobby__check_all_ready">check_all_ready()</a></dt></h4><dd>
<p><span>check_all_ready(self) -&gt; bool</span></p>

<p>Return whether all choosers are marked ready.</p>

</dd>
<dt><h4><a name="method_ba_Lobby__create_join_info">create_join_info()</a></dt></h4><dd>
<p><span>create_join_info(self) -&gt; JoinInfo</span></p>

<p>Create a display of on-screen information for joiners.</p>

<p>(how to switch teams, players, etc.)
Intended for use in initial joining-screens.</p>

</dd>
<dt><h4><a name="method_ba_Lobby__get_choosers">get_choosers()</a></dt></h4><dd>
<p><span>get_choosers(self) -&gt; List[Chooser]</span></p>

<p>Return the lobby's current choosers.</p>

</dd>
<dt><h4><a name="method_ba_Lobby__reload_profiles">reload_profiles()</a></dt></h4><dd>
<p><span>reload_profiles(self) -&gt; None</span></p>

<p>Reload available player profiles.</p>

</dd>
<dt><h4><a name="method_ba_Lobby__remove_all_choosers">remove_all_choosers()</a></dt></h4><dd>
<p><span>remove_all_choosers(self) -&gt; None</span></p>

<p>Remove all choosers without kicking players.</p>

<p>This is called after all players check in and enter a game.</p>

</dd>
<dt><h4><a name="method_ba_Lobby__remove_all_choosers_and_kick_players">remove_all_choosers_and_kick_players()</a></dt></h4><dd>
<p><span>remove_all_choosers_and_kick_players(self) -&gt; None</span></p>

<p>Remove all player choosers and kick attached players.</p>

</dd>
<dt><h4><a name="method_ba_Lobby__remove_chooser">remove_chooser()</a></dt></h4><dd>
<p><span>remove_chooser(self, player: <a href="#class_ba_SessionPlayer">ba.SessionPlayer</a>) -&gt; None</span></p>

<p>Remove a single player's chooser; does not kick them.</p>

<p>This is used when a player enters the game and no longer
needs a chooser.</p>

</dd>
<dt><h4><a name="method_ba_Lobby__update_positions">update_positions()</a></dt></h4><dd>
<p><span>update_positions(self) -&gt; None</span></p>

<p>Update positions for all choosers.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_Lstr">ba.Lstr</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Used to define strings in a language-independent way.</p>

<p>Category: <a href="#class_category_General_Utility_Classes">General Utility Classes</a></p>

<p>    These should be used whenever possible in place of hard-coded strings
    so that in-game or UI elements show up correctly on all clients in their
    currently-active language.</p>

<p>    To see available resource keys, look at any of the bs_language_*.py files
    in the game or the translations pages at bombsquadgame.com/translate.</p>

<pre><span><em><small>    # EXAMPLE 1: specify a string from a resource path</small></em></span>
    mynode.text = <a href="#class_ba_Lstr">ba.Lstr</a>(resource='audioSettingsWindow.titleText')</pre>

<pre><span><em><small>    # EXAMPLE 2: specify a translated string via a category and english value;</small></em></span>
<span><em><small>    # if a translated value is available, it will be used; otherwise the</small></em></span>
<span><em><small>    # english value will be. To see available translation categories, look</small></em></span>
<span><em><small>    # under the 'translations' resource section.</small></em></span>
    mynode.text = <a href="#class_ba_Lstr">ba.Lstr</a>(translate=('gameDescriptions', 'Defeat all enemies'))</pre>

<pre><span><em><small>    # EXAMPLE 3: specify a raw value and some substitutions.  Substitutions can</small></em></span>
<span><em><small>    # be used with resource and translate modes as well.</small></em></span>
    mynode.text = <a href="#class_ba_Lstr">ba.Lstr</a>(value='${A} / ${B}',
                          subs=[('${A}', str(score)), ('${B}', str(total))])</pre>

<pre><span><em><small>    # EXAMPLE 4: Lstrs can be nested.  This example would display the resource</small></em></span>
<span><em><small>    # at res_a but replace ${NAME} with the value of the resource at res_b</small></em></span>
    mytextnode.text = <a href="#class_ba_Lstr">ba.Lstr</a>(resource='res_a',
                              subs=[('${NAME}', <a href="#class_ba_Lstr">ba.Lstr</a>(resource='res_b'))])
</pre>

<h3>Methods:</h3>
<h5><a href="#method_ba_Lstr____init__">&lt;constructor&gt;</a>, <a href="#method_ba_Lstr__evaluate">evaluate()</a>, <a href="#method_ba_Lstr__from_json">from_json()</a>, <a href="#method_ba_Lstr__is_flat_value">is_flat_value()</a></h5>
<dl>
<dt><h4><a name="method_ba_Lstr____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.Lstr(*args: Any, **keywds: Any)</span></p>

<p>Instantiate a Lstr.</p>

<p>Pass a value for either 'resource', 'translate',
or 'value'. (see Lstr help for examples).
'subs' can be a sequence of 2-member sequences consisting of values
and replacements.
'fallback_resource' can be a resource key that will be used if the
main one is not present for
the current language in place of falling back to the english value
('resource' mode only).
'fallback_value' can be a literal string that will be used if neither
the resource nor the fallback resource is found ('resource' mode only).</p>

</dd>
<dt><h4><a name="method_ba_Lstr__evaluate">evaluate()</a></dt></h4><dd>
<p><span>evaluate(self) -&gt; str</span></p>

<p>Evaluate the Lstr and returns a flat string in the current language.</p>

<p>You should avoid doing this as much as possible and instead pass
and store Lstr values.</p>

</dd>
<dt><h4><a name="method_ba_Lstr__from_json">from_json()</a></dt></h4><dd>
<p><span>from_json(json_string: str) -&gt; <a href="#class_ba_Lstr">ba.Lstr</a></span></p>

<p>Given a json string, returns a <a href="#class_ba_Lstr">ba.Lstr</a>. Does no data validation.</p>

</dd>
<dt><h4><a name="method_ba_Lstr__is_flat_value">is_flat_value()</a></dt></h4><dd>
<p><span>is_flat_value(self) -&gt; bool</span></p>

<p>Return whether the Lstr is a 'flat' value.</p>

<p>This is defined as a simple string value incorporating no translations,
resources, or substitutions.  In this case it may be reasonable to
replace it with a raw string value, perform string manipulation on it,
etc.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_Map">ba.Map</a></strong></h3>
<p>Inherits from: <a href="#class_ba_Actor">ba.Actor</a></p>
<p>A game map.</p>

<p>Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a></p>

<p>    Consists of a collection of terrain nodes, metadata, and other
    functionality comprising a game map.
</p>

<h3>Attributes:</h3>
<h5><a href="#attr_ba_Map__activity">activity</a>, <a href="#attr_ba_Map__expired">expired</a></h5>
<dl>
<dt><h4><a name="attr_ba_Map__activity">activity</a></h4></dt><dd>
<p><span><a href="#class_ba_Activity">ba.Activity</a></span></p>
<p>The Activity this Actor was created in.</p>

<p>        Raises a <a href="#class_ba_ActivityNotFoundError">ba.ActivityNotFoundError</a> if the Activity no longer exists.</p>

</dd>
<dt><h4><a name="attr_ba_Map__expired">expired</a></h4></dt><dd>
<p><span>bool</span></p>
<p>Whether the Actor is expired.</p>

<p>        (see <a href="#method_ba_Actor__on_expire">ba.Actor.on_expire</a>())</p>

</dd>
</dl>
<h3>Methods Inherited:</h3>
<h5><a href="#method_ba_Actor__autoretain">autoretain()</a>, <a href="#method_ba_Actor__getactivity">getactivity()</a>, <a href="#method_ba_Actor__is_alive">is_alive()</a>, <a href="#method_ba_Actor__on_expire">on_expire()</a></h5>
<h3>Methods Defined or Overridden:</h3>
<h5><a href="#method_ba_Map____init__">&lt;constructor&gt;</a>, <a href="#method_ba_Map__exists">exists()</a>, <a href="#method_ba_Map__get_def_bound_box">get_def_bound_box()</a>, <a href="#method_ba_Map__get_def_point">get_def_point()</a>, <a href="#method_ba_Map__get_def_points">get_def_points()</a>, <a href="#method_ba_Map__get_ffa_start_position">get_ffa_start_position()</a>, <a href="#method_ba_Map__get_flag_position">get_flag_position()</a>, <a href="#method_ba_Map__get_music_type">get_music_type()</a>, <a href="#method_ba_Map__get_play_types">get_play_types()</a>, <a href="#method_ba_Map__get_preview_texture_name">get_preview_texture_name()</a>, <a href="#method_ba_Map__get_start_position">get_start_position()</a>, <a href="#method_ba_Map__getname">getname()</a>, <a href="#method_ba_Map__handlemessage">handlemessage()</a>, <a href="#method_ba_Map__is_point_near_edge">is_point_near_edge()</a>, <a href="#method_ba_Map__on_preload">on_preload()</a>, <a href="#method_ba_Map__preload">preload()</a></h5>
<dl>
<dt><h4><a name="method_ba_Map____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.Map(vr_overlay_offset: Optional[Sequence[float]] = None)</span></p>

<p>Instantiate a map.</p>

</dd>
<dt><h4><a name="method_ba_Map__exists">exists()</a></dt></h4><dd>
<p><span>exists(self) -&gt; bool</span></p>

<p>Returns whether the Actor is still present in a meaningful way.</p>

<p>Note that a dying character should still return True here as long as
their corpse is visible; this is about presence, not being 'alive'
(see <a href="#method_ba_Actor__is_alive">ba.Actor.is_alive</a>() for that).</p>

<p>If this returns False, it is assumed the Actor can be completely
deleted without affecting the game; this call is often used
when pruning lists of Actors, such as with <a href="#method_ba_Actor__autoretain">ba.Actor.autoretain</a>()</p>

<p>The default implementation of this method always return True.</p>

<p>Note that the boolean operator for the Actor class calls this method,
so a simple "if myactor" test will conveniently do the right thing
even if myactor is set to None.</p>

</dd>
<dt><h4><a name="method_ba_Map__get_def_bound_box">get_def_bound_box()</a></dt></h4><dd>
<p><span>get_def_bound_box(self, name: str) -&gt; Optional[Tuple[float, float, float, float, float, float]]</span></p>

<p>Return a 6 member bounds tuple or None if it is not defined.</p>

</dd>
<dt><h4><a name="method_ba_Map__get_def_point">get_def_point()</a></dt></h4><dd>
<p><span>get_def_point(self, name: str) -&gt; Optional[Sequence[float]]</span></p>

<p>Return a single defined point or a default value in its absence.</p>

</dd>
<dt><h4><a name="method_ba_Map__get_def_points">get_def_points()</a></dt></h4><dd>
<p><span>get_def_points(self, name: str) -&gt; List[Sequence[float]]</span></p>

<p>Return a list of named points.</p>

<p>Return as many sequential ones are defined (flag1, flag2, flag3), etc.
If none are defined, returns an empty list.</p>

</dd>
<dt><h4><a name="method_ba_Map__get_ffa_start_position">get_ffa_start_position()</a></dt></h4><dd>
<p><span>get_ffa_start_position(self, players: Sequence[<a href="#class_ba_Player">ba.Player</a>]) -&gt; Sequence[float]</span></p>

<p>Return a random starting position in one of the FFA spawn areas.</p>

<p>If a list of <a href="#class_ba_Player">ba.Players</a> is provided; the returned points will be
as far from these players as possible.</p>

</dd>
<dt><h4><a name="method_ba_Map__get_flag_position">get_flag_position()</a></dt></h4><dd>
<p><span>get_flag_position(self, team_index: int = None) -&gt; Sequence[float]</span></p>

<p>Return a flag position on the map for the given team index.</p>

<p>Pass None to get the default flag point.
(used for things such as king-of-the-hill)</p>

</dd>
<dt><h4><a name="method_ba_Map__get_music_type">get_music_type()</a></dt></h4><dd>
<h5><span><em>&lt;class method&gt;</span></em></h5>
<p><span>get_music_type() -&gt; Optional[<a href="#class_ba_MusicType">ba.MusicType</a>] </span></p>

<p>Return a music-type string that should be played on this map.</p>

<p>If None is returned, default music will be used.</p>

</dd>
<dt><h4><a name="method_ba_Map__get_play_types">get_play_types()</a></dt></h4><dd>
<h5><span><em>&lt;class method&gt;</span></em></h5>
<p><span>get_play_types() -&gt; List[str] </span></p>

<p>Return valid play types for this map.</p>

</dd>
<dt><h4><a name="method_ba_Map__get_preview_texture_name">get_preview_texture_name()</a></dt></h4><dd>
<h5><span><em>&lt;class method&gt;</span></em></h5>
<p><span>get_preview_texture_name() -&gt; Optional[str] </span></p>

<p>Return the name of the preview texture for this map.</p>

</dd>
<dt><h4><a name="method_ba_Map__get_start_position">get_start_position()</a></dt></h4><dd>
<p><span>get_start_position(self, team_index: int) -&gt; Sequence[float]</span></p>

<p>Return a random starting position for the given team index.</p>

</dd>
<dt><h4><a name="method_ba_Map__getname">getname()</a></dt></h4><dd>
<h5><span><em>&lt;class method&gt;</span></em></h5>
<p><span>getname() -&gt; str </span></p>

<p>Return the unique name of this map, in English.</p>

</dd>
<dt><h4><a name="method_ba_Map__handlemessage">handlemessage()</a></dt></h4><dd>
<p><span>handlemessage(self, msg: Any) -&gt; Any</span></p>

<p>General message handling; can be passed any <a href="#class_category_Message_Classes">message object</a>.</p>

</dd>
<dt><h4><a name="method_ba_Map__is_point_near_edge">is_point_near_edge()</a></dt></h4><dd>
<p><span>is_point_near_edge(self, point: <a href="#class_ba_Vec3">ba.Vec3</a>, running: bool = False) -&gt; bool</span></p>

<p>Return whether the provided point is near an edge of the map.</p>

<p>Simple bot logic uses this call to determine if they
are approaching a cliff or wall. If this returns True they will
generally not walk/run any farther away from the origin.
If 'running' is True, the buffer should be a bit larger.</p>

</dd>
<dt><h4><a name="method_ba_Map__on_preload">on_preload()</a></dt></h4><dd>
<h5><span><em>&lt;class method&gt;</span></em></h5>
<p><span>on_preload() -&gt; Any </span></p>

<p>Called when the map is being preloaded.</p>

<p>It should return any media/data it requires to operate</p>

</dd>
<dt><h4><a name="method_ba_Map__preload">preload()</a></dt></h4><dd>
<h5><span><em>&lt;class method&gt;</span></em></h5>
<p><span>preload() -&gt; None </span></p>

<p>Preload map media.</p>

<p>This runs the class's on_preload() method as needed to prep it to run.
Preloading should generally be done in a <a href="#class_ba_Activity">ba.Activity</a>'s __init__ method.
Note that this is a classmethod since it is not operate on map
instances but rather on the class itself before instances are made</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_Material">ba.Material</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Material(label: str = None)</p>

<p>An entity applied to game objects to modify collision behavior.</p>

<p>Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a></p>

<p>A material can affect physical characteristics, generate sounds,
or trigger callback functions when collisions occur.</p>

<p>Materials are applied to 'parts', which are groups of one or more
rigid bodies created as part of a <a href="#class_ba_Node">ba.Node</a>.  Nodes can have any number
of parts, each with its own set of materials. Generally materials are
specified as array attributes on the Node. The 'spaz' node, for
example, has various attributes such as 'materials',
'roller_materials', and 'punch_materials', which correspond to the
various parts it creates.</p>

<p>Use <a href="#class_ba_Material">ba.Material</a>() to instantiate a blank material, and then use its
add_actions() method to define what the material does.</p>

<h3>Attributes:</h3>
<dl>
<dt><h4><a name="attr_ba_Material__label">label</a></h4></dt><dd>
<p><span> str</span></p>
<p>A label for the material; only used for debugging.</p>

</dd>
</dl>
<h3>Methods:</h3>
<dl>
<dt><h4><a name="method_ba_Material__add_actions">add_actions()</a></dt></h4><dd>
<p><span>add_actions(actions: Tuple, conditions: Optional[Tuple] = None)
  -&gt; None</span></p>

<p>Add one or more actions to the material, optionally with conditions.</p>

<p><strong>Conditions:</strong></p>

<p>Conditions are provided as tuples which can be combined to form boolean
logic. A single condition might look like ('condition_name', cond_arg),
or a more complex nested one might look like (('some_condition',
cond_arg), 'or', ('another_condition', cond2_arg)).</p>

<p>'and', 'or', and 'xor' are available to chain together 2 conditions, as
  seen above.</p>

<p><strong>Available Conditions:</strong></p>

<p>('they_have_material', material) - does the part we're hitting have a
  given <a href="#class_ba_Material">ba.Material</a>?</p>

<p>('they_dont_have_material', material) - does the part we're hitting
  not have a given <a href="#class_ba_Material">ba.Material</a>?</p>

<p>('eval_colliding') - is 'collide' true at this point in material
  evaluation? (see the modify_part_collision action)</p>

<p>('eval_not_colliding') - is 'collide' false at this point in material
  evaluation? (see the modify_part_collision action)</p>

<p>('we_are_younger_than', age) - is our part younger than 'age'
  (in milliseconds)?</p>

<p>('we_are_older_than', age) - is our part older than 'age'
  (in milliseconds)?</p>

<p>('they_are_younger_than', age) - is the part we're hitting younger than
  'age' (in milliseconds)?</p>

<p>('they_are_older_than', age) - is the part we're hitting older than
  'age' (in milliseconds)?</p>

<p>('they_are_same_node_as_us') - does the part we're hitting belong to
  the same <a href="#class_ba_Node">ba.Node</a> as us?</p>

<p>('they_are_different_node_than_us') - does the part we're hitting
  belong to a different <a href="#class_ba_Node">ba.Node</a> than us?</p>

<p><strong>Actions:</strong></p>

<p>In a similar manner, actions are specified as tuples. Multiple actions
can be specified by providing a tuple of tuples.</p>

<p><strong>Available Actions:</strong></p>

<p>('call', when, callable) - calls the provided callable; 'when' can be
  either 'at_connect' or 'at_disconnect'. 'at_connect' means to fire
  when the two parts first come in contact; 'at_disconnect' means to
  fire once they cease being in contact.</p>

<p>('message', who, when, message_obj) - sends a message object; 'who' can
  be either 'our_node' or 'their_node', 'when' can be 'at_connect' or
  'at_disconnect', and message_obj is the message object to send.
  This has the same effect as calling the node's handlemessage()
  method.</p>

<p>('modify_part_collision', attr, value) - changes some characteristic
  of the physical collision that will occur between our part and their
  part.  This change will remain in effect as long as the two parts
  remain overlapping. This means if you have a part with a material
  that turns 'collide' off against parts younger than 100ms, and it
  touches another part that is 50ms old, it will continue to not
  collide with that part until they separate, even if the 100ms
  threshold is passed. Options for attr/value are: 'physical' (boolean
  value; whether a *physical* response will occur at all), 'friction'
  (float value; how friction-y the physical response will be),
  'collide' (boolean value; whether *any* collision will occur at all,
  including non-physical stuff like callbacks), 'use_node_collide'
  (boolean value; whether to honor modify_node_collision overrides for
  this collision), 'stiffness' (float value, how springy the physical
  response is), 'damping' (float value, how damped the physical
  response is), 'bounce' (float value; how bouncy the physical response
  is).</p>

<p>('modify_node_collision', attr, value) - similar to
  modify_part_collision, but operates at a node-level.
  collision attributes set here will remain in effect as long as
  *anything* from our part's node and their part's node overlap.
  A key use of this functionality is to prevent new nodes from
  colliding with each other if they appear overlapped;
  if modify_part_collision is used, only the individual parts that
  were overlapping would avoid contact, but other parts could still
  contact leaving the two nodes 'tangled up'.  Using
  modify_node_collision ensures that the nodes must completely
  separate before they can start colliding.  Currently the only attr
  available here is 'collide' (a boolean value).</p>

<p>('sound', sound, volume) - plays a <a href="#class_ba_Sound">ba.Sound</a> when a collision occurs, at
  a given volume, regardless of the collision speed/etc.</p>

<p>('impact_sound', sound, targetImpulse, volume) - plays a sound when a
  collision occurs, based on the speed of impact. Provide a <a href="#class_ba_Sound">ba.Sound</a>, a
  target-impulse, and a volume.</p>

<p>('skid_sound', sound, targetImpulse, volume) - plays a sound during a
  collision when parts are 'scraping' against each other. Provide a
  <a href="#class_ba_Sound">ba.Sound</a>, a target-impulse, and a volume.</p>

<p>('roll_sound', sound, targetImpulse, volume) - plays a sound during a
  collision when parts are 'rolling' against each other. Provide a
  <a href="#class_ba_Sound">ba.Sound</a>, a target-impulse, and a volume.</p>

<pre><span><em><small># example 1: create a material that lets us ignore</small></em></span>
<span><em><small># collisions against any nodes we touch in the first</small></em></span>
<span><em><small># 100 ms of our existence; handy for preventing us from</small></em></span>
<span><em><small># exploding outward if we spawn on top of another object:</small></em></span>
m = <a href="#class_ba_Material">ba.Material</a>()
m.add_actions(conditions=(('we_are_younger_than', 100),
                         'or',('they_are_younger_than', 100)),
             actions=('modify_node_collision', 'collide', False))</pre>

<pre><span><em><small># example 2: send a DieMessage to anything we touch, but cause</small></em></span>
<span><em><small># no physical response.  This should cause any <a href="#class_ba_Actor">ba.Actor</a> to drop dead:</small></em></span>
m = <a href="#class_ba_Material">ba.Material</a>()
m.add_actions(actions=(('modify_part_collision', 'physical', False),
                      ('message', 'their_node', 'at_connect',
                       <a href="#class_ba_DieMessage">ba.DieMessage</a>())))</pre>

<pre><span><em><small># example 3: play some sounds when we're contacting the ground:</small></em></span>
m = <a href="#class_ba_Material">ba.Material</a>()
m.add_actions(conditions=('they_have_material',
                          shared.footing_material),
              actions=(('impact_sound', <a href="#function_ba_getsound">ba.getsound</a>('metalHit'), 2, 5),
                       ('skid_sound', <a href="#function_ba_getsound">ba.getsound</a>('metalSkid'), 2, 5)))</pre>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_MetadataSubsystem">ba.MetadataSubsystem</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Subsystem for working with script metadata in the app.</p>

<p>Category: <a href="#class_category_App_Classes">App Classes</a></p>

<p>    Access the single shared instance of this class at 'ba.app.meta'.
</p>

<h3>Methods:</h3>
<h5><a href="#method_ba_MetadataSubsystem____init__">&lt;constructor&gt;</a>, <a href="#method_ba_MetadataSubsystem__get_game_types">get_game_types()</a>, <a href="#method_ba_MetadataSubsystem__get_scan_results">get_scan_results()</a>, <a href="#method_ba_MetadataSubsystem__get_unowned_game_types">get_unowned_game_types()</a>, <a href="#method_ba_MetadataSubsystem__handle_scan_results">handle_scan_results()</a>, <a href="#method_ba_MetadataSubsystem__on_app_launch">on_app_launch()</a>, <a href="#method_ba_MetadataSubsystem__start_scan">start_scan()</a></h5>
<dl>
<dt><h4><a name="method_ba_MetadataSubsystem____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.MetadataSubsystem()</span></p>

</dd>
<dt><h4><a name="method_ba_MetadataSubsystem__get_game_types">get_game_types()</a></dt></h4><dd>
<p><span>get_game_types(self) -&gt; List[Type[<a href="#class_ba_GameActivity">ba.GameActivity</a>]]</span></p>

<p>Return available game types.</p>

</dd>
<dt><h4><a name="method_ba_MetadataSubsystem__get_scan_results">get_scan_results()</a></dt></h4><dd>
<p><span>get_scan_results(self) -&gt; ScanResults</span></p>

<p>Return meta scan results; block if the scan is not yet complete.</p>

</dd>
<dt><h4><a name="method_ba_MetadataSubsystem__get_unowned_game_types">get_unowned_game_types()</a></dt></h4><dd>
<p><span>get_unowned_game_types(self) -&gt; Set[Type[<a href="#class_ba_GameActivity">ba.GameActivity</a>]]</span></p>

<p>Return present game types not owned by the current account.</p>

</dd>
<dt><h4><a name="method_ba_MetadataSubsystem__handle_scan_results">handle_scan_results()</a></dt></h4><dd>
<p><span>handle_scan_results(self, results: ScanResults) -&gt; None</span></p>

<p>Called in the game thread with results of a completed scan.</p>

</dd>
<dt><h4><a name="method_ba_MetadataSubsystem__on_app_launch">on_app_launch()</a></dt></h4><dd>
<p><span>on_app_launch(self) -&gt; None</span></p>

<p>Should be called when the app is done bootstrapping.</p>

</dd>
<dt><h4><a name="method_ba_MetadataSubsystem__start_scan">start_scan()</a></dt></h4><dd>
<p><span>start_scan(self) -&gt; None</span></p>

<p>Begin scanning script directories for scripts containing metadata.</p>

<p>Should be called only once at launch.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_Model">ba.Model</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>A reference to a model.</p>

<p>Category: <a href="#class_category_Asset_Classes">Asset Classes</a></p>

<p>Models are used for drawing.
Use <a href="#function_ba_getmodel">ba.getmodel</a>() to instantiate one.</p>

<hr>
<h2><strong><a name="class_ba_MultiTeamSession">ba.MultiTeamSession</a></strong></h3>
<p>Inherits from: <a href="#class_ba_Session">ba.Session</a></p>
<p>Common base class for <a href="#class_ba_DualTeamSession">ba.DualTeamSession</a> and <a href="#class_ba_FreeForAllSession">ba.FreeForAllSession</a>.</p>

<p>Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a></p>

<p>    Free-for-all-mode is essentially just teams-mode with each <a href="#class_ba_Player">ba.Player</a> having
    their own <a href="#class_ba_Team">ba.Team</a>, so there is much overlap in functionality.
</p>

<h3>Attributes Inherited:</h3>
<h5><a href="#attr_ba_Session__allow_mid_activity_joins">allow_mid_activity_joins</a>, <a href="#attr_ba_Session__customdata">customdata</a>, <a href="#attr_ba_Session__lobby">lobby</a>, <a href="#attr_ba_Session__max_players">max_players</a>, <a href="#attr_ba_Session__min_players">min_players</a>, <a href="#attr_ba_Session__sessionplayers">sessionplayers</a>, <a href="#attr_ba_Session__sessionteams">sessionteams</a>, <a href="#attr_ba_Session__use_team_colors">use_team_colors</a>, <a href="#attr_ba_Session__use_teams">use_teams</a></h5>
<h3>Attributes Defined Here:</h3>
<dl>
<dt><h4><a name="attr_ba_MultiTeamSession__sessionglobalsnode">sessionglobalsnode</a></h4></dt><dd>
<p><span><a href="#class_ba_Node">ba.Node</a></span></p>
<p>The sessionglobals <a href="#class_ba_Node">ba.Node</a> for the session.</p>

</dd>
</dl>
<h3>Methods Inherited:</h3>
<h5><a href="#method_ba_Session__begin_next_activity">begin_next_activity()</a>, <a href="#method_ba_Session__end">end()</a>, <a href="#method_ba_Session__end_activity">end_activity()</a>, <a href="#method_ba_Session__get_custom_menu_entries">get_custom_menu_entries()</a>, <a href="#method_ba_Session__getactivity">getactivity()</a>, <a href="#method_ba_Session__handlemessage">handlemessage()</a>, <a href="#method_ba_Session__on_player_leave">on_player_leave()</a>, <a href="#method_ba_Session__on_player_request">on_player_request()</a>, <a href="#method_ba_Session__on_team_leave">on_team_leave()</a>, <a href="#method_ba_Session__setactivity">setactivity()</a>, <a href="#method_ba_Session__transitioning_out_activity_was_freed">transitioning_out_activity_was_freed()</a></h5>
<h3>Methods Defined or Overridden:</h3>
<h5><a href="#method_ba_MultiTeamSession____init__">&lt;constructor&gt;</a>, <a href="#method_ba_MultiTeamSession__announce_game_results">announce_game_results()</a>, <a href="#method_ba_MultiTeamSession__get_ffa_series_length">get_ffa_series_length()</a>, <a href="#method_ba_MultiTeamSession__get_game_number">get_game_number()</a>, <a href="#method_ba_MultiTeamSession__get_max_players">get_max_players()</a>, <a href="#method_ba_MultiTeamSession__get_next_game_description">get_next_game_description()</a>, <a href="#method_ba_MultiTeamSession__get_series_length">get_series_length()</a>, <a href="#method_ba_MultiTeamSession__on_activity_end">on_activity_end()</a>, <a href="#method_ba_MultiTeamSession__on_team_join">on_team_join()</a></h5>
<dl>
<dt><h4><a name="method_ba_MultiTeamSession____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.MultiTeamSession()</span></p>

<p>Set up playlists and launches a <a href="#class_ba_Activity">ba.Activity</a> to accept joiners.</p>

</dd>
<dt><h4><a name="method_ba_MultiTeamSession__announce_game_results">announce_game_results()</a></dt></h4><dd>
<p><span>announce_game_results(self, activity: <a href="#class_ba_GameActivity">ba.GameActivity</a>, results: <a href="#class_ba_GameResults">ba.GameResults</a>, delay: float, announce_winning_team: bool = True) -&gt; None</span></p>

<p>Show basic game result at the end of a game.</p>

<p>(before transitioning to a score screen).
This will include a zoom-text of 'BLUE WINS'
or whatnot, along with a possible audio
announcement of the same.</p>

</dd>
<dt><h4><a name="method_ba_MultiTeamSession__get_ffa_series_length">get_ffa_series_length()</a></dt></h4><dd>
<p><span>get_ffa_series_length(self) -&gt; int</span></p>

<p>Return free-for-all series length.</p>

</dd>
<dt><h4><a name="method_ba_MultiTeamSession__get_game_number">get_game_number()</a></dt></h4><dd>
<p><span>get_game_number(self) -&gt; int</span></p>

<p>Returns which game in the series is currently being played.</p>

</dd>
<dt><h4><a name="method_ba_MultiTeamSession__get_max_players">get_max_players()</a></dt></h4><dd>
<p><span>get_max_players(self) -&gt; int</span></p>

<p>Return max number of <a href="#class_ba_Player">ba.Players</a> allowed to join the game at once.</p>

</dd>
<dt><h4><a name="method_ba_MultiTeamSession__get_next_game_description">get_next_game_description()</a></dt></h4><dd>
<p><span>get_next_game_description(self) -&gt; <a href="#class_ba_Lstr">ba.Lstr</a></span></p>

<p>Returns a description of the next game on deck.</p>

</dd>
<dt><h4><a name="method_ba_MultiTeamSession__get_series_length">get_series_length()</a></dt></h4><dd>
<p><span>get_series_length(self) -&gt; int</span></p>

<p>Return teams series length.</p>

</dd>
<dt><h4><a name="method_ba_MultiTeamSession__on_activity_end">on_activity_end()</a></dt></h4><dd>
<p><span>on_activity_end(self, activity: <a href="#class_ba_Activity">ba.Activity</a>, results: Any) -&gt; None</span></p>

<p>Called when the current <a href="#class_ba_Activity">ba.Activity</a> has ended.</p>

<p>The <a href="#class_ba_Session">ba.Session</a> should look at the results and start
another <a href="#class_ba_Activity">ba.Activity</a>.</p>

</dd>
<dt><h4><a name="method_ba_MultiTeamSession__on_team_join">on_team_join()</a></dt></h4><dd>
<p><span>on_team_join(self, team: <a href="#class_ba_SessionTeam">ba.SessionTeam</a>) -&gt; None</span></p>

<p>Called when a new <a href="#class_ba_Team">ba.Team</a> joins the session.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_MusicPlayer">ba.MusicPlayer</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Wrangles soundtrack music playback.</p>

<p>Category: <a href="#class_category_App_Classes">App Classes</a></p>

<p>    Music can be played either through the game itself
    or via a platform-specific external player.
</p>

<h3>Methods:</h3>
<h5><a href="#method_ba_MusicPlayer____init__">&lt;constructor&gt;</a>, <a href="#method_ba_MusicPlayer__on_app_shutdown">on_app_shutdown()</a>, <a href="#method_ba_MusicPlayer__on_play">on_play()</a>, <a href="#method_ba_MusicPlayer__on_select_entry">on_select_entry()</a>, <a href="#method_ba_MusicPlayer__on_set_volume">on_set_volume()</a>, <a href="#method_ba_MusicPlayer__on_stop">on_stop()</a>, <a href="#method_ba_MusicPlayer__play">play()</a>, <a href="#method_ba_MusicPlayer__select_entry">select_entry()</a>, <a href="#method_ba_MusicPlayer__set_volume">set_volume()</a>, <a href="#method_ba_MusicPlayer__shutdown">shutdown()</a>, <a href="#method_ba_MusicPlayer__stop">stop()</a></h5>
<dl>
<dt><h4><a name="method_ba_MusicPlayer____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.MusicPlayer()</span></p>

</dd>
<dt><h4><a name="method_ba_MusicPlayer__on_app_shutdown">on_app_shutdown()</a></dt></h4><dd>
<p><span>on_app_shutdown(self) -&gt; None</span></p>

<p>Called on final app shutdown.</p>

</dd>
<dt><h4><a name="method_ba_MusicPlayer__on_play">on_play()</a></dt></h4><dd>
<p><span>on_play(self, entry: Any) -&gt; None</span></p>

<p>Called when a new song/playlist/etc should be played.</p>

</dd>
<dt><h4><a name="method_ba_MusicPlayer__on_select_entry">on_select_entry()</a></dt></h4><dd>
<p><span>on_select_entry(self, callback: Callable[[Any], None], current_entry: Any, selection_target_name: str) -&gt; Any</span></p>

<p>Present a GUI to select an entry.</p>

<p>The callback should be called with a valid entry or None to
signify that the default soundtrack should be used..</p>

</dd>
<dt><h4><a name="method_ba_MusicPlayer__on_set_volume">on_set_volume()</a></dt></h4><dd>
<p><span>on_set_volume(self, volume: float) -&gt; None</span></p>

<p>Called when the volume should be changed.</p>

</dd>
<dt><h4><a name="method_ba_MusicPlayer__on_stop">on_stop()</a></dt></h4><dd>
<p><span>on_stop(self) -&gt; None</span></p>

<p>Called when the music should stop.</p>

</dd>
<dt><h4><a name="method_ba_MusicPlayer__play">play()</a></dt></h4><dd>
<p><span>play(self, entry: Any) -&gt; None</span></p>

<p>Play provided entry.</p>

</dd>
<dt><h4><a name="method_ba_MusicPlayer__select_entry">select_entry()</a></dt></h4><dd>
<p><span>select_entry(self, callback: Callable[[Any], None], current_entry: Any, selection_target_name: str) -&gt; Any</span></p>

<p>Summons a UI to select a new soundtrack entry.</p>

</dd>
<dt><h4><a name="method_ba_MusicPlayer__set_volume">set_volume()</a></dt></h4><dd>
<p><span>set_volume(self, volume: float) -&gt; None</span></p>

<p>Set player volume (value should be between 0 and 1).</p>

</dd>
<dt><h4><a name="method_ba_MusicPlayer__shutdown">shutdown()</a></dt></h4><dd>
<p><span>shutdown(self) -&gt; None</span></p>

<p>Shutdown music playback completely.</p>

</dd>
<dt><h4><a name="method_ba_MusicPlayer__stop">stop()</a></dt></h4><dd>
<p><span>stop(self) -&gt; None</span></p>

<p>Stop any playback that is occurring.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_MusicPlayMode">ba.MusicPlayMode</a></strong></h3>
<p>Inherits from: <a href="https://docs.python.org/3/library/enum.html#enum.Enum">enum.Enum</a></p>
<p>Influences behavior when playing music.</p>

<p>Category: <a href="#class_category_Enums">Enums</a>
</p>

<h3>Values:</h3>
<ul>
<li>REGULAR</li>
<li>TEST</li>
</ul>
<hr>
<h2><strong><a name="class_ba_MusicSubsystem">ba.MusicSubsystem</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Subsystem for music playback in the app.</p>

<p>Category: <a href="#class_category_App_Classes">App Classes</a></p>

<p>    Access the single shared instance of this class at 'ba.app.music'.
</p>

<h3>Methods:</h3>
<h5><a href="#method_ba_MusicSubsystem____init__">&lt;constructor&gt;</a>, <a href="#method_ba_MusicSubsystem__do_play_music">do_play_music()</a>, <a href="#method_ba_MusicSubsystem__get_music_player">get_music_player()</a>, <a href="#method_ba_MusicSubsystem__get_soundtrack_entry_name">get_soundtrack_entry_name()</a>, <a href="#method_ba_MusicSubsystem__get_soundtrack_entry_type">get_soundtrack_entry_type()</a>, <a href="#method_ba_MusicSubsystem__have_music_player">have_music_player()</a>, <a href="#method_ba_MusicSubsystem__music_volume_changed">music_volume_changed()</a>, <a href="#method_ba_MusicSubsystem__on_app_launch">on_app_launch()</a>, <a href="#method_ba_MusicSubsystem__on_app_resume">on_app_resume()</a>, <a href="#method_ba_MusicSubsystem__on_app_shutdown">on_app_shutdown()</a>, <a href="#method_ba_MusicSubsystem__set_music_play_mode">set_music_play_mode()</a>, <a href="#method_ba_MusicSubsystem__supports_soundtrack_entry_type">supports_soundtrack_entry_type()</a></h5>
<dl>
<dt><h4><a name="method_ba_MusicSubsystem____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.MusicSubsystem()</span></p>

</dd>
<dt><h4><a name="method_ba_MusicSubsystem__do_play_music">do_play_music()</a></dt></h4><dd>
<p><span>do_play_music(self, musictype: Union[MusicType, str, None], continuous: bool = False, mode: MusicPlayMode = &lt;MusicPlayMode.REGULAR: regular&gt;, testsoundtrack: Dict[str, Any] = None) -&gt; None</span></p>

<p>Plays the requested music type/mode.</p>

<p>For most cases, setmusic() is the proper call to use, which itself
calls this. Certain cases, however, such as soundtrack testing, may
require calling this directly.</p>

</dd>
<dt><h4><a name="method_ba_MusicSubsystem__get_music_player">get_music_player()</a></dt></h4><dd>
<p><span>get_music_player(self) -&gt; MusicPlayer</span></p>

<p>Returns the system music player, instantiating if necessary.</p>

</dd>
<dt><h4><a name="method_ba_MusicSubsystem__get_soundtrack_entry_name">get_soundtrack_entry_name()</a></dt></h4><dd>
<p><span>get_soundtrack_entry_name(self, entry: Any) -&gt; str</span></p>

<p>Given a soundtrack entry, returns its name.</p>

</dd>
<dt><h4><a name="method_ba_MusicSubsystem__get_soundtrack_entry_type">get_soundtrack_entry_type()</a></dt></h4><dd>
<p><span>get_soundtrack_entry_type(self, entry: Any) -&gt; str</span></p>

<p>Given a soundtrack entry, returns its type, taking into
account what is supported locally.</p>

</dd>
<dt><h4><a name="method_ba_MusicSubsystem__have_music_player">have_music_player()</a></dt></h4><dd>
<p><span>have_music_player(self) -&gt; bool</span></p>

<p>Returns whether a music player is present.</p>

</dd>
<dt><h4><a name="method_ba_MusicSubsystem__music_volume_changed">music_volume_changed()</a></dt></h4><dd>
<p><span>music_volume_changed(self, val: float) -&gt; None</span></p>

<p>Should be called when changing the music volume.</p>

</dd>
<dt><h4><a name="method_ba_MusicSubsystem__on_app_launch">on_app_launch()</a></dt></h4><dd>
<p><span>on_app_launch(self) -&gt; None</span></p>

<p>Should be called by app on_app_launch().</p>

</dd>
<dt><h4><a name="method_ba_MusicSubsystem__on_app_resume">on_app_resume()</a></dt></h4><dd>
<p><span>on_app_resume(self) -&gt; None</span></p>

<p>Should be run when the app resumes from a suspended state.</p>

</dd>
<dt><h4><a name="method_ba_MusicSubsystem__on_app_shutdown">on_app_shutdown()</a></dt></h4><dd>
<p><span>on_app_shutdown(self) -&gt; None</span></p>

<p>Should be called when the app is shutting down.</p>

</dd>
<dt><h4><a name="method_ba_MusicSubsystem__set_music_play_mode">set_music_play_mode()</a></dt></h4><dd>
<p><span>set_music_play_mode(self, mode: MusicPlayMode, force_restart: bool = False) -&gt; None</span></p>

<p>Sets music play mode; used for soundtrack testing/etc.</p>

</dd>
<dt><h4><a name="method_ba_MusicSubsystem__supports_soundtrack_entry_type">supports_soundtrack_entry_type()</a></dt></h4><dd>
<p><span>supports_soundtrack_entry_type(self, entry_type: str) -&gt; bool</span></p>

<p>Return whether provided soundtrack entry type is supported here.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_MusicType">ba.MusicType</a></strong></h3>
<p>Inherits from: <a href="https://docs.python.org/3/library/enum.html#enum.Enum">enum.Enum</a></p>
<p>Types of music available to play in-game.</p>

<p>Category: <a href="#class_category_Enums">Enums</a></p>

<p>    These do not correspond to specific pieces of music, but rather to
    'situations'. The actual music played for each type can be overridden
    by the game or by the user.
</p>

<h3>Values:</h3>
<ul>
<li>MENU</li>
<li>VICTORY</li>
<li>CHAR_SELECT</li>
<li>RUN_AWAY</li>
<li>ONSLAUGHT</li>
<li>KEEP_AWAY</li>
<li>RACE</li>
<li>EPIC_RACE</li>
<li>SCORES</li>
<li>GRAND_ROMP</li>
<li>TO_THE_DEATH</li>
<li>CHOSEN_ONE</li>
<li>FORWARD_MARCH</li>
<li>FLAG_CATCHER</li>
<li>SURVIVAL</li>
<li>EPIC</li>
<li>SPORTS</li>
<li>HOCKEY</li>
<li>FOOTBALL</li>
<li>FLYING</li>
<li>SCARY</li>
<li>MARCHING</li>
</ul>
<hr>
<h2><strong><a name="class_ba_Node">ba.Node</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Reference to a Node; the low level building block of the game.</p>

<p>Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a></p>

<p>At its core, a game is nothing more than a scene of Nodes
with attributes getting interconnected or set over time.</p>

<p>A <a href="#class_ba_Node">ba.Node</a> instance should be thought of as a weak-reference
to a game node; *not* the node itself. This means a Node's
lifecycle is completely independent of how many Python references
to it exist. To explicitly add a new node to the game, use
<a href="#function_ba_newnode">ba.newnode</a>(), and to explicitly delete one, use <a href="#method_ba_Node__delete">ba.Node.delete</a>().
<a href="#method_ba_Node__exists">ba.Node.exists</a>() can be used to determine if a Node still points to
a live node in the game.</p>

<p>You can use <a href="#class_ba_Node">ba.Node</a>(None) to instantiate an invalid
Node reference (sometimes used as attr values/etc).</p>

<h3>Methods:</h3>
<h5><a href="#method_ba_Node__add_death_action">add_death_action()</a>, <a href="#method_ba_Node__connectattr">connectattr()</a>, <a href="#method_ba_Node__delete">delete()</a>, <a href="#method_ba_Node__exists">exists()</a>, <a href="#method_ba_Node__getdelegate">getdelegate()</a>, <a href="#method_ba_Node__getname">getname()</a>, <a href="#method_ba_Node__getnodetype">getnodetype()</a>, <a href="#method_ba_Node__handlemessage">handlemessage()</a></h5>
<dl>
<dt><h4><a name="method_ba_Node__add_death_action">add_death_action()</a></dt></h4><dd>
<p><span>add_death_action(action: Callable[[], None]) -&gt; None</span></p>

<p>Add a callable object to be called upon this node's death.
Note that these actions are run just after the node dies, not before.</p>

</dd>
<dt><h4><a name="method_ba_Node__connectattr">connectattr()</a></dt></h4><dd>
<p><span>connectattr(srcattr: str, dstnode: Node, dstattr: str) -&gt; None</span></p>

<p>Connect one of this node's attributes to an attribute on another node.
This will immediately set the target attribute's value to that of the
source attribute, and will continue to do so once per step as long as
the two nodes exist.  The connection can be severed by setting the
target attribute to any value or connecting another node attribute
to it.</p>

<pre><span><em><small># Example: create a locator and attach a light to it:</small></em></span>
light = <a href="#function_ba_newnode">ba.newnode</a>('light')
loc = <a href="#function_ba_newnode">ba.newnode</a>('locator', attrs={'position': (0,10,0)})
loc.connectattr('position', light, 'position')</pre>

</dd>
<dt><h4><a name="method_ba_Node__delete">delete()</a></dt></h4><dd>
<p><span>delete(ignore_missing: bool = True) -&gt; None</span></p>

<p>Delete the node.  Ignores already-deleted nodes if ignore_missing
is True; otherwise a <a href="#class_ba_NodeNotFoundError">ba.NodeNotFoundError</a> is thrown.</p>

</dd>
<dt><h4><a name="method_ba_Node__exists">exists()</a></dt></h4><dd>
<p><span>exists() -&gt; bool</span></p>

<p>Returns whether the Node still exists.
Most functionality will fail on a nonexistent Node, so it's never a bad
idea to check this.</p>

<p>Note that you can also use the boolean operator for this same
functionality, so a statement such as "if mynode" will do
the right thing both for Node objects and values of None.</p>

</dd>
<dt><h4><a name="method_ba_Node__getdelegate">getdelegate()</a></dt></h4><dd>
<p><span>getdelegate(type: Type, doraise: bool = False) -&gt; &lt;varies&gt;</span></p>

<p>Return the node's current delegate object if it matches a certain type.</p>

<p>If the node has no delegate or it is not an instance of the passed
type, then None will be returned. If 'doraise' is True, then an
<a href="#class_ba_DelegateNotFoundError">ba.DelegateNotFoundError</a> will be raised instead.</p>

</dd>
<dt><h4><a name="method_ba_Node__getname">getname()</a></dt></h4><dd>
<p><span>getname() -&gt; str</span></p>

<p>Return the name assigned to a Node; used mainly for debugging</p>

</dd>
<dt><h4><a name="method_ba_Node__getnodetype">getnodetype()</a></dt></h4><dd>
<p><span>getnodetype() -&gt; str</span></p>

<p>Return the type of Node referenced by this object as a string.
(Note this is different from the Python type which is always <a href="#class_ba_Node">ba.Node</a>)</p>

</dd>
<dt><h4><a name="method_ba_Node__handlemessage">handlemessage()</a></dt></h4><dd>
<p><span>handlemessage(*args: Any) -&gt; None</span></p>

<p>General message handling; can be passed any <a href="#class_category_Message_Classes">message object</a>.</p>

<p>All standard message objects are forwarded along to the <a href="#class_ba_Node">ba.Node</a>'s
delegate for handling (generally the <a href="#class_ba_Actor">ba.Actor</a> that made the node).</p>

<p><a href="#class_ba_Node">ba.Nodes</a> are unique, however, in that they can be passed a second
form of message; 'node-messages'.  These consist of a string type-name
as a first argument along with the args specific to that type name
as additional arguments.
Node-messages communicate directly with the low-level node layer
and are delivered simultaneously on all game clients,
acting as an alternative to setting node attributes.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_NodeActor">ba.NodeActor</a></strong></h3>
<p>Inherits from: <a href="#class_ba_Actor">ba.Actor</a></p>
<p>A simple <a href="#class_ba_Actor">ba.Actor</a> type that wraps a single <a href="#class_ba_Node">ba.Node</a>.</p>

<p>Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a></p>

<p>    This Actor will delete its Node when told to die, and it's
    exists() call will return whether the Node still exists or not.
</p>

<h3>Attributes:</h3>
<h5><a href="#attr_ba_NodeActor__activity">activity</a>, <a href="#attr_ba_NodeActor__expired">expired</a></h5>
<dl>
<dt><h4><a name="attr_ba_NodeActor__activity">activity</a></h4></dt><dd>
<p><span><a href="#class_ba_Activity">ba.Activity</a></span></p>
<p>The Activity this Actor was created in.</p>

<p>        Raises a <a href="#class_ba_ActivityNotFoundError">ba.ActivityNotFoundError</a> if the Activity no longer exists.</p>

</dd>
<dt><h4><a name="attr_ba_NodeActor__expired">expired</a></h4></dt><dd>
<p><span>bool</span></p>
<p>Whether the Actor is expired.</p>

<p>        (see <a href="#method_ba_Actor__on_expire">ba.Actor.on_expire</a>())</p>

</dd>
</dl>
<h3>Methods Inherited:</h3>
<h5><a href="#method_ba_Actor__autoretain">autoretain()</a>, <a href="#method_ba_Actor__getactivity">getactivity()</a>, <a href="#method_ba_Actor__is_alive">is_alive()</a>, <a href="#method_ba_Actor__on_expire">on_expire()</a></h5>
<h3>Methods Defined or Overridden:</h3>
<h5><a href="#method_ba_NodeActor____init__">&lt;constructor&gt;</a>, <a href="#method_ba_NodeActor__exists">exists()</a>, <a href="#method_ba_NodeActor__handlemessage">handlemessage()</a></h5>
<dl>
<dt><h4><a name="method_ba_NodeActor____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.NodeActor(node: <a href="#class_ba_Node">ba.Node</a>)</span></p>

<p>Instantiates an Actor in the current <a href="#class_ba_Activity">ba.Activity</a>.</p>

</dd>
<dt><h4><a name="method_ba_NodeActor__exists">exists()</a></dt></h4><dd>
<p><span>exists(self) -&gt; bool</span></p>

<p>Returns whether the Actor is still present in a meaningful way.</p>

<p>Note that a dying character should still return True here as long as
their corpse is visible; this is about presence, not being 'alive'
(see <a href="#method_ba_Actor__is_alive">ba.Actor.is_alive</a>() for that).</p>

<p>If this returns False, it is assumed the Actor can be completely
deleted without affecting the game; this call is often used
when pruning lists of Actors, such as with <a href="#method_ba_Actor__autoretain">ba.Actor.autoretain</a>()</p>

<p>The default implementation of this method always return True.</p>

<p>Note that the boolean operator for the Actor class calls this method,
so a simple "if myactor" test will conveniently do the right thing
even if myactor is set to None.</p>

</dd>
<dt><h4><a name="method_ba_NodeActor__handlemessage">handlemessage()</a></dt></h4><dd>
<p><span>handlemessage(self, msg: Any) -&gt; Any</span></p>

<p>General message handling; can be passed any <a href="#class_category_Message_Classes">message object</a>.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_NodeNotFoundError">ba.NodeNotFoundError</a></strong></h3>
<p>Inherits from: <a href="#class_ba_NotFoundError">ba.NotFoundError</a>, <a href="https://docs.python.org/3/library/exceptions.html#Exception">Exception</a>, <a href="https://docs.python.org/3/library/exceptions.html#BaseException">BaseException</a></p>
<p>Exception raised when an expected <a href="#class_ba_Node">ba.Node</a> does not exist.</p>

<p>Category: <a href="#class_category_Exception_Classes">Exception Classes</a>
</p>

<h3>Methods:</h3>
<p>&lt;all methods inherited from <a href="#class_ba_NotFoundError">ba.NotFoundError</a>&gt;</p>
<hr>
<h2><strong><a name="class_ba_NotFoundError">ba.NotFoundError</a></strong></h3>
<p>Inherits from: <a href="https://docs.python.org/3/library/exceptions.html#Exception">Exception</a>, <a href="https://docs.python.org/3/library/exceptions.html#BaseException">BaseException</a></p>
<p>Exception raised when a referenced object does not exist.</p>

<p>Category: <a href="#class_category_Exception_Classes">Exception Classes</a>
</p>

<h3>Methods:</h3>
<p>&lt;all methods inherited from <a href="https://docs.python.org/3/library/exceptions.html#Exception">Exception</a>&gt;</p>
<hr>
<h2><strong><a name="class_ba_OutOfBoundsMessage">ba.OutOfBoundsMessage</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>A message telling an object that it is out of bounds.</p>

<p>Category: <a href="#class_category_Message_Classes">Message Classes</a>
</p>

<h3>Methods:</h3>
<dl>
<dt><h4><a name="method_ba_OutOfBoundsMessage____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.OutOfBoundsMessage()</span></p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_Permission">ba.Permission</a></strong></h3>
<p>Inherits from: <a href="https://docs.python.org/3/library/enum.html#enum.Enum">enum.Enum</a></p>
<p>Permissions that can be requested from the OS.</p>

<p>Category: <a href="#class_category_Enums">Enums</a>
</p>

<h3>Values:</h3>
<ul>
<li>STORAGE</li>
</ul>
<hr>
<h2><strong><a name="class_ba_PickedUpMessage">ba.PickedUpMessage</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Tells an object that it has been picked up by something.</p>

<p>Category: <a href="#class_category_Message_Classes">Message Classes</a></p>

<h3>Attributes:</h3>
<dl>
<dt><h4><a name="attr_ba_PickedUpMessage__node">node</a></h4></dt><dd>
<p><span><a href="#class_ba_Node">ba.Node</a></span></p>
<p>The <a href="#class_ba_Node">ba.Node</a> doing the picking up.</p>

</dd>
</dl>
<h3>Methods:</h3>
<dl>
<dt><h4><a name="method_ba_PickedUpMessage____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.PickedUpMessage(node: <a href="#class_ba_Node">ba.Node</a>)</span></p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_PickUpMessage">ba.PickUpMessage</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Tells an object that it has picked something up.</p>

<p>Category: <a href="#class_category_Message_Classes">Message Classes</a></p>

<h3>Attributes:</h3>
<dl>
<dt><h4><a name="attr_ba_PickUpMessage__node">node</a></h4></dt><dd>
<p><span><a href="#class_ba_Node">ba.Node</a></span></p>
<p>The <a href="#class_ba_Node">ba.Node</a> that is getting picked up.</p>

</dd>
</dl>
<h3>Methods:</h3>
<dl>
<dt><h4><a name="method_ba_PickUpMessage____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.PickUpMessage(node: <a href="#class_ba_Node">ba.Node</a>)</span></p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_Player">ba.Player</a></strong></h3>
<p>Inherits from: <a href="https://docs.python.org/3/library/typing.html#typing.Generic">typing.Generic</a></p>
<p>A player in a specific <a href="#class_ba_Activity">ba.Activity</a>.</p>

<p>Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a></p>

<p>    These correspond to <a href="#class_ba_SessionPlayer">ba.SessionPlayer</a> objects, but are associated with a
    single <a href="#class_ba_Activity">ba.Activity</a> instance. This allows activities to specify their
    own custom <a href="#class_ba_Player">ba.Player</a> types.</p>

<h3>Attributes:</h3>
<h5><a href="#attr_ba_Player__actor">actor</a>, <a href="#attr_ba_Player__customdata">customdata</a>, <a href="#attr_ba_Player__node">node</a>, <a href="#attr_ba_Player__position">position</a>, <a href="#attr_ba_Player__sessionplayer">sessionplayer</a>, <a href="#attr_ba_Player__team">team</a></h5>
<dl>
<dt><h4><a name="attr_ba_Player__actor">actor</a></h4></dt><dd>
<p><span>Optional[<a href="#class_ba_Actor">ba.Actor</a>]</span></p>
<p>The <a href="#class_ba_Actor">ba.Actor</a> associated with the player.</p>

</dd>
<dt><h4><a name="attr_ba_Player__customdata">customdata</a></h4></dt><dd>
<p><span>dict</span></p>
<p>Arbitrary values associated with the player.
        Though it is encouraged that most player values be properly defined
        on the <a href="#class_ba_Player">ba.Player</a> subclass, it may be useful for player-agnostic
        objects to store values here. This dict is cleared when the player
        leaves or expires so objects stored here will be disposed of at
        the expected time, unlike the Player instance itself which may
        continue to be referenced after it is no longer part of the game.</p>

</dd>
<dt><h4><a name="attr_ba_Player__node">node</a></h4></dt><dd>
<p><span><a href="#class_ba_Node">ba.Node</a></span></p>
<p>A <a href="#class_ba_Node">ba.Node</a> of type 'player' associated with this Player.</p>

<p>        This node can be used to get a generic player position/etc.</p>

</dd>
<dt><h4><a name="attr_ba_Player__position">position</a></h4></dt><dd>
<p><span><a href="#class_ba_Vec3">ba.Vec3</a></span></p>
<p>The position of the player, as defined by its current <a href="#class_ba_Actor">ba.Actor</a>.</p>

<p>        If the player currently has no actor, raises a <a href="#class_ba_ActorNotFoundError">ba.ActorNotFoundError</a>.</p>

</dd>
<dt><h4><a name="attr_ba_Player__sessionplayer">sessionplayer</a></h4></dt><dd>
<p><span><a href="#class_ba_SessionPlayer">ba.SessionPlayer</a></span></p>
<p>Return the <a href="#class_ba_SessionPlayer">ba.SessionPlayer</a> corresponding to this Player.</p>

<p>        Throws a <a href="#class_ba_SessionPlayerNotFoundError">ba.SessionPlayerNotFoundError</a> if it does not exist.</p>

</dd>
<dt><h4><a name="attr_ba_Player__team">team</a></h4></dt><dd>
<p><span>TeamType</span></p>
<p>The <a href="#class_ba_Team">ba.Team</a> for this player.</p>

</dd>
</dl>
<h3>Methods:</h3>
<h5><a href="#method_ba_Player__assigninput">assigninput()</a>, <a href="#method_ba_Player__exists">exists()</a>, <a href="#method_ba_Player__get_icon">get_icon()</a>, <a href="#method_ba_Player__getname">getname()</a>, <a href="#method_ba_Player__is_alive">is_alive()</a>, <a href="#method_ba_Player__on_expire">on_expire()</a>, <a href="#method_ba_Player__resetinput">resetinput()</a></h5>
<dl>
<dt><h4><a name="method_ba_Player__assigninput">assigninput()</a></dt></h4><dd>
<p><span>assigninput(self, inputtype: Union[<a href="#class_ba_InputType">ba.InputType</a>, Tuple[<a href="#class_ba_InputType">ba.InputType</a>, ...]], call: Callable) -&gt; None</span></p>

<p>assigninput(type: Union[<a href="#class_ba_InputType">ba.InputType</a>, Tuple[<a href="#class_ba_InputType">ba.InputType</a>, ...]],
  call: Callable) -&gt; None</p>

<p>Set the python callable to be run for one or more types of input.</p>

</dd>
<dt><h4><a name="method_ba_Player__exists">exists()</a></dt></h4><dd>
<p><span>exists(self) -&gt; bool</span></p>

<p>Whether the underlying player still exists.</p>

<p>This will return False if the underlying <a href="#class_ba_SessionPlayer">ba.SessionPlayer</a> has
left the game or if the <a href="#class_ba_Activity">ba.Activity</a> this player was associated
with has ended.
Most functionality will fail on a nonexistent player.
Note that you can also use the boolean operator for this same
functionality, so a statement such as "if player" will do
the right thing both for Player objects and values of None.</p>

</dd>
<dt><h4><a name="method_ba_Player__get_icon">get_icon()</a></dt></h4><dd>
<p><span>get_icon(self) -&gt; Dict[str, Any]</span></p>

<p>get_icon() -&gt; Dict[str, Any]</p>

<p>Returns the character's icon (images, colors, etc contained in a dict)</p>

</dd>
<dt><h4><a name="method_ba_Player__getname">getname()</a></dt></h4><dd>
<p><span>getname(self, full: bool = False, icon: bool = True) -&gt; str</span></p>

<p>getname(full: bool = False, icon: bool = True) -&gt; str</p>

<p>Returns the player's name. If icon is True, the long version of the
name may include an icon.</p>

</dd>
<dt><h4><a name="method_ba_Player__is_alive">is_alive()</a></dt></h4><dd>
<p><span>is_alive(self) -&gt; bool</span></p>

<p>is_alive() -&gt; bool</p>

<p>Returns True if the player has a <a href="#class_ba_Actor">ba.Actor</a> assigned and its
is_alive() method return True. False is returned otherwise.</p>

</dd>
<dt><h4><a name="method_ba_Player__on_expire">on_expire()</a></dt></h4><dd>
<p><span>on_expire(self) -&gt; None</span></p>

<p>Can be overridden to handle player expiration.</p>

<p>The player expires when the Activity it is a part of expires.
Expired players should no longer run any game logic (which will
likely error). They should, however, remove any references to
players/teams/games/etc. which could prevent them from being freed.</p>

</dd>
<dt><h4><a name="method_ba_Player__resetinput">resetinput()</a></dt></h4><dd>
<p><span>resetinput(self) -&gt; None</span></p>

<p>resetinput() -&gt; None</p>

<p>Clears out the player's assigned input actions.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_PlayerDiedMessage">ba.PlayerDiedMessage</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>A message saying a <a href="#class_ba_Player">ba.Player</a> has died.</p>

<p>Category: <a href="#class_category_Message_Classes">Message Classes</a></p>

<h3>Attributes:</h3>
<h5><a href="#attr_ba_PlayerDiedMessage__how">how</a>, <a href="#attr_ba_PlayerDiedMessage__killed">killed</a></h5>
<dl>
<dt><h4><a name="attr_ba_PlayerDiedMessage__how">how</a></h4></dt><dd>
<p><span><a href="#class_ba_DeathType">ba.DeathType</a></span></p>
<p>The particular type of death.</p>

</dd>
<dt><h4><a name="attr_ba_PlayerDiedMessage__killed">killed</a></h4></dt><dd>
<p><span>bool</span></p>
<p>If True, the player was killed;
If False, they left the game or the round ended.</p>

</dd>
</dl>
<h3>Methods:</h3>
<h5><a href="#method_ba_PlayerDiedMessage____init__">&lt;constructor&gt;</a>, <a href="#method_ba_PlayerDiedMessage__getkillerplayer">getkillerplayer()</a>, <a href="#method_ba_PlayerDiedMessage__getplayer">getplayer()</a></h5>
<dl>
<dt><h4><a name="method_ba_PlayerDiedMessage____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.PlayerDiedMessage(player: <a href="#class_ba_Player">ba.Player</a>, was_killed: bool, killerplayer: Optional[<a href="#class_ba_Player">ba.Player</a>], how: <a href="#class_ba_DeathType">ba.DeathType</a>)</span></p>

<p>Instantiate a message with the given values.</p>

</dd>
<dt><h4><a name="method_ba_PlayerDiedMessage__getkillerplayer">getkillerplayer()</a></dt></h4><dd>
<p><span>getkillerplayer(self, playertype: Type[PlayerType]) -&gt; Optional[PlayerType]</span></p>

<p>Return the <a href="#class_ba_Player">ba.Player</a> responsible for the killing, if any.</p>

<p>Pass the Player type being used by the current game.</p>

</dd>
<dt><h4><a name="method_ba_PlayerDiedMessage__getplayer">getplayer()</a></dt></h4><dd>
<p><span>getplayer(self, playertype: Type[PlayerType]) -&gt; PlayerType</span></p>

<p>Return the <a href="#class_ba_Player">ba.Player</a> that died.</p>

<p>The type of player for the current activity should be passed so that
the type-checker properly identifies the returned value as one.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_PlayerInfo">ba.PlayerInfo</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Holds basic info about a player.</p>

<p>Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a>
</p>

<h3>Methods:</h3>
<dl>
<dt><h4><a name="method_ba_PlayerInfo____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.PlayerInfo(name: str, character: str)</span></p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_PlayerNotFoundError">ba.PlayerNotFoundError</a></strong></h3>
<p>Inherits from: <a href="#class_ba_NotFoundError">ba.NotFoundError</a>, <a href="https://docs.python.org/3/library/exceptions.html#Exception">Exception</a>, <a href="https://docs.python.org/3/library/exceptions.html#BaseException">BaseException</a></p>
<p>Exception raised when an expected <a href="#class_ba_Player">ba.Player</a> does not exist.</p>

<p>Category: <a href="#class_category_Exception_Classes">Exception Classes</a>
</p>

<h3>Methods:</h3>
<p>&lt;all methods inherited from <a href="#class_ba_NotFoundError">ba.NotFoundError</a>&gt;</p>
<hr>
<h2><strong><a name="class_ba_PlayerRecord">ba.PlayerRecord</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Stats for an individual player in a <a href="#class_ba_Stats">ba.Stats</a> object.</p>

<p>Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a></p>

<p>    This does not necessarily correspond to a <a href="#class_ba_Player">ba.Player</a> that is
    still present (stats may be retained for players that leave
    mid-game)
</p>

<h3>Attributes:</h3>
<h5><a href="#attr_ba_PlayerRecord__player">player</a>, <a href="#attr_ba_PlayerRecord__team">team</a></h5>
<dl>
<dt><h4><a name="attr_ba_PlayerRecord__player">player</a></h4></dt><dd>
<p><span><a href="#class_ba_SessionPlayer">ba.SessionPlayer</a></span></p>
<p>Return the instance's associated <a href="#class_ba_SessionPlayer">ba.SessionPlayer</a>.</p>

<p>        Raises a <a href="#class_ba_SessionPlayerNotFoundError">ba.SessionPlayerNotFoundError</a> if the player
        no longer exists.</p>

</dd>
<dt><h4><a name="attr_ba_PlayerRecord__team">team</a></h4></dt><dd>
<p><span><a href="#class_ba_SessionTeam">ba.SessionTeam</a></span></p>
<p>The <a href="#class_ba_SessionTeam">ba.SessionTeam</a> the last associated player was last on.</p>

<p>        This can still return a valid result even if the player is gone.
        Raises a <a href="#class_ba_SessionTeamNotFoundError">ba.SessionTeamNotFoundError</a> if the team no longer exists.</p>

</dd>
</dl>
<h3>Methods:</h3>
<h5><a href="#method_ba_PlayerRecord____init__">&lt;constructor&gt;</a>, <a href="#method_ba_PlayerRecord__associate_with_sessionplayer">associate_with_sessionplayer()</a>, <a href="#method_ba_PlayerRecord__cancel_multi_kill_timer">cancel_multi_kill_timer()</a>, <a href="#method_ba_PlayerRecord__get_icon">get_icon()</a>, <a href="#method_ba_PlayerRecord__get_last_sessionplayer">get_last_sessionplayer()</a>, <a href="#method_ba_PlayerRecord__getactivity">getactivity()</a>, <a href="#method_ba_PlayerRecord__getname">getname()</a>, <a href="#method_ba_PlayerRecord__submit_kill">submit_kill()</a></h5>
<dl>
<dt><h4><a name="method_ba_PlayerRecord____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.PlayerRecord(name: str, name_full: str, sessionplayer: <a href="#class_ba_SessionPlayer">ba.SessionPlayer</a>, stats: <a href="#class_ba_Stats">ba.Stats</a>)</span></p>

</dd>
<dt><h4><a name="method_ba_PlayerRecord__associate_with_sessionplayer">associate_with_sessionplayer()</a></dt></h4><dd>
<p><span>associate_with_sessionplayer(self, sessionplayer: <a href="#class_ba_SessionPlayer">ba.SessionPlayer</a>) -&gt; None</span></p>

<p>Associate this entry with a <a href="#class_ba_SessionPlayer">ba.SessionPlayer</a>.</p>

</dd>
<dt><h4><a name="method_ba_PlayerRecord__cancel_multi_kill_timer">cancel_multi_kill_timer()</a></dt></h4><dd>
<p><span>cancel_multi_kill_timer(self) -&gt; None</span></p>

<p>Cancel any multi-kill timer for this player entry.</p>

</dd>
<dt><h4><a name="method_ba_PlayerRecord__get_icon">get_icon()</a></dt></h4><dd>
<p><span>get_icon(self) -&gt; Dict[str, Any]</span></p>

<p>Get the icon for this instance's player.</p>

</dd>
<dt><h4><a name="method_ba_PlayerRecord__get_last_sessionplayer">get_last_sessionplayer()</a></dt></h4><dd>
<p><span>get_last_sessionplayer(self) -&gt; <a href="#class_ba_SessionPlayer">ba.SessionPlayer</a></span></p>

<p>Return the last <a href="#class_ba_Player">ba.Player</a> we were associated with.</p>

</dd>
<dt><h4><a name="method_ba_PlayerRecord__getactivity">getactivity()</a></dt></h4><dd>
<p><span>getactivity(self) -&gt; Optional[<a href="#class_ba_Activity">ba.Activity</a>]</span></p>

<p>Return the <a href="#class_ba_Activity">ba.Activity</a> this instance is currently associated with.</p>

<p>Returns None if the activity no longer exists.</p>

</dd>
<dt><h4><a name="method_ba_PlayerRecord__getname">getname()</a></dt></h4><dd>
<p><span>getname(self, full: bool = False) -&gt; str</span></p>

<p>Return the player entry's name.</p>

</dd>
<dt><h4><a name="method_ba_PlayerRecord__submit_kill">submit_kill()</a></dt></h4><dd>
<p><span>submit_kill(self, showpoints: bool = True) -&gt; None</span></p>

<p>Submit a kill for this player entry.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_PlayerScoredMessage">ba.PlayerScoredMessage</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Informs something that a <a href="#class_ba_Player">ba.Player</a> scored.</p>

<p>Category: <a href="#class_category_Message_Classes">Message Classes</a></p>

<h3>Attributes:</h3>
<dl>
<dt><h4><a name="attr_ba_PlayerScoredMessage__score">score</a></h4></dt><dd>
<p><span>int</span></p>
<p>The score value.</p>

</dd>
</dl>
<h3>Methods:</h3>
<dl>
<dt><h4><a name="method_ba_PlayerScoredMessage____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.PlayerScoredMessage(score: int)</span></p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_Plugin">ba.Plugin</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>A plugin to alter app behavior in some way.</p>

<p>Category: <a href="#class_category_App_Classes">App Classes</a></p>

<p>    Plugins are discoverable by the meta-tag system
    and the user can select which ones they want to activate.
    Active plugins are then called at specific times as the
    app is running in order to modify its behavior in some way.
</p>

<h3>Methods:</h3>
<h5><a href="#method_ba_Plugin__on_app_launch">on_app_launch()</a>, <a href="#method_ba_Plugin__on_app_pause">on_app_pause()</a>, <a href="#method_ba_Plugin__on_app_resume">on_app_resume()</a>, <a href="#method_ba_Plugin__on_app_shutdown">on_app_shutdown()</a></h5>
<dl>
<dt><h4><a name="method_ba_Plugin__on_app_launch">on_app_launch()</a></dt></h4><dd>
<p><span>on_app_launch(self) -&gt; None</span></p>

<p>Called when the app is being launched.</p>

</dd>
<dt><h4><a name="method_ba_Plugin__on_app_pause">on_app_pause()</a></dt></h4><dd>
<p><span>on_app_pause(self) -&gt; None</span></p>

<p>Called after pausing game activity.</p>

</dd>
<dt><h4><a name="method_ba_Plugin__on_app_resume">on_app_resume()</a></dt></h4><dd>
<p><span>on_app_resume(self) -&gt; None</span></p>

<p>Called after the game continues.</p>

</dd>
<dt><h4><a name="method_ba_Plugin__on_app_shutdown">on_app_shutdown()</a></dt></h4><dd>
<p><span>on_app_shutdown(self) -&gt; None</span></p>

<p>Called before closing the application.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_PluginSubsystem">ba.PluginSubsystem</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Subsystem for plugin handling in the app.</p>

<p>Category: <a href="#class_category_App_Classes">App Classes</a></p>

<p>    Access the single shared instance of this class at 'ba.app.plugins'.
</p>

<h3>Methods:</h3>
<h5><a href="#method_ba_PluginSubsystem____init__">&lt;constructor&gt;</a>, <a href="#method_ba_PluginSubsystem__on_app_launch">on_app_launch()</a>, <a href="#method_ba_PluginSubsystem__on_app_pause">on_app_pause()</a>, <a href="#method_ba_PluginSubsystem__on_app_resume">on_app_resume()</a>, <a href="#method_ba_PluginSubsystem__on_app_shutdown">on_app_shutdown()</a></h5>
<dl>
<dt><h4><a name="method_ba_PluginSubsystem____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.PluginSubsystem()</span></p>

</dd>
<dt><h4><a name="method_ba_PluginSubsystem__on_app_launch">on_app_launch()</a></dt></h4><dd>
<p><span>on_app_launch(self) -&gt; None</span></p>

<p>Should be called at app launch time.</p>

</dd>
<dt><h4><a name="method_ba_PluginSubsystem__on_app_pause">on_app_pause()</a></dt></h4><dd>
<p><span>on_app_pause(self) -&gt; None</span></p>

<p>Called when the app goes to a suspended state.</p>

</dd>
<dt><h4><a name="method_ba_PluginSubsystem__on_app_resume">on_app_resume()</a></dt></h4><dd>
<p><span>on_app_resume(self) -&gt; None</span></p>

<p>Run when the app resumes from a suspended state.</p>

</dd>
<dt><h4><a name="method_ba_PluginSubsystem__on_app_shutdown">on_app_shutdown()</a></dt></h4><dd>
<p><span>on_app_shutdown(self) -&gt; None</span></p>

<p>Called when the app is being closed.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_PotentialPlugin">ba.PotentialPlugin</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Represents a <a href="#class_ba_Plugin">ba.Plugin</a> which can potentially be loaded.</p>

<p>Category: <a href="#class_category_App_Classes">App Classes</a></p>

<p>    These generally represent plugins which were detected by the
    meta-tag scan. However they may also represent plugins which
    were previously set to be loaded but which were unable to be
    for some reason. In that case, 'available' will be set to False.
</p>

<h3>Methods:</h3>
<dl>
<dt><h4><a name="method_ba_PotentialPlugin____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.PotentialPlugin(display_name: <a href="#class_ba_Lstr">ba.Lstr</a>, class_path: str, available: bool)</span></p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_PowerupAcceptMessage">ba.PowerupAcceptMessage</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>A message informing a ba.Powerup that it was accepted.</p>

<p>Category: <a href="#class_category_Message_Classes">Message Classes</a></p>

<p>    This is generally sent in response to a <a href="#class_ba_PowerupMessage">ba.PowerupMessage</a>
    to inform the box (or whoever granted it) that it can go away.
</p>

<h3>Methods:</h3>
<dl>
<dt><h4><a name="method_ba_PowerupAcceptMessage____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.PowerupAcceptMessage()</span></p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_PowerupMessage">ba.PowerupMessage</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>A message telling an object to accept a powerup.</p>

<p>Category: <a href="#class_category_Message_Classes">Message Classes</a></p>

<p>    This message is normally received by touching a ba.PowerupBox.</p>

<h3>Attributes:</h3>
<h5><a href="#attr_ba_PowerupMessage__poweruptype">poweruptype</a>, <a href="#attr_ba_PowerupMessage__sourcenode">sourcenode</a></h5>
<dl>
<dt><h4><a name="attr_ba_PowerupMessage__poweruptype">poweruptype</a></h4></dt><dd>
<p><span>str</span></p>
<p>The type of powerup to be granted (a string).
See ba.Powerup.poweruptype for available type values.</p>

</dd>
<dt><h4><a name="attr_ba_PowerupMessage__sourcenode">sourcenode</a></h4></dt><dd>
<p><span>Optional[<a href="#class_ba_Node">ba.Node</a>]</span></p>
<p>The node the powerup game from, or None otherwise.
If a powerup is accepted, a <a href="#class_ba_PowerupAcceptMessage">ba.PowerupAcceptMessage</a> should be sent
back to the sourcenode to inform it of the fact. This will generally
cause the powerup box to make a sound and disappear or whatnot.</p>

</dd>
</dl>
<h3>Methods:</h3>
<dl>
<dt><h4><a name="method_ba_PowerupMessage____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.PowerupMessage(poweruptype: str, sourcenode: Optional[<a href="#class_ba_Node">ba.Node</a>] = None)</span></p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_ScoreConfig">ba.ScoreConfig</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Settings for how a game handles scores.</p>

<p>Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a></p>

<h3>Attributes:</h3>
<h5><a href="#attr_ba_ScoreConfig__label">label</a>, <a href="#attr_ba_ScoreConfig__lower_is_better">lower_is_better</a>, <a href="#attr_ba_ScoreConfig__none_is_winner">none_is_winner</a>, <a href="#attr_ba_ScoreConfig__scoretype">scoretype</a>, <a href="#attr_ba_ScoreConfig__version">version</a></h5>
<dl>
<dt><h4><a name="attr_ba_ScoreConfig__label">label</a></h4></dt><dd>
<p><span>str</span></p>
<p>A label show to the user for scores; 'Score', 'Time Survived', etc.</p>

</dd>
<dt><h4><a name="attr_ba_ScoreConfig__lower_is_better">lower_is_better</a></h4></dt><dd>
<p><span>bool</span></p>
<p>Whether lower scores are preferable. Higher scores are by default.</p>

</dd>
<dt><h4><a name="attr_ba_ScoreConfig__none_is_winner">none_is_winner</a></h4></dt><dd>
<p><span>bool</span></p>
<p>Whether a value of None is considered better than other scores.
By default it is not.</p>

</dd>
<dt><h4><a name="attr_ba_ScoreConfig__scoretype">scoretype</a></h4></dt><dd>
<p><span><a href="#class_ba_ScoreType">ba.ScoreType</a></span></p>
<p>How the score value should be displayed.</p>

</dd>
<dt><h4><a name="attr_ba_ScoreConfig__version">version</a></h4></dt><dd>
<p><span>str</span></p>
<p>To change high-score lists used by a game without renaming the game,
change this. Defaults to an empty string.</p>

</dd>
</dl>
<h3>Methods:</h3>
<dl>
<dt><h4><a name="method_ba_ScoreConfig____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.ScoreConfig(label: 'str' = 'Score', scoretype: '<a href="#class_ba_ScoreType">ba.ScoreType</a>' = &lt;ScoreType.POINTS: 'p'&gt;, lower_is_better: 'bool' = False, none_is_winner: 'bool' = False, version: 'str' = '')</span></p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_ScoreType">ba.ScoreType</a></strong></h3>
<p>Inherits from: <a href="https://docs.python.org/3/library/enum.html#enum.Enum">enum.Enum</a></p>
<p>Type of scores.</p>

<p>Category: <a href="#class_category_Enums">Enums</a>
</p>

<h3>Values:</h3>
<ul>
<li>SECONDS</li>
<li>MILLISECONDS</li>
<li>POINTS</li>
</ul>
<hr>
<h2><strong><a name="class_ba_ServerController">ba.ServerController</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Overall controller for the app in server mode.</p>

<p>Category: <a href="#class_category_App_Classes">App Classes</a>
</p>

<h3>Methods:</h3>
<h5><a href="#method_ba_ServerController____init__">&lt;constructor&gt;</a>, <a href="#method_ba_ServerController__handle_transition">handle_transition()</a>, <a href="#method_ba_ServerController__kick">kick()</a>, <a href="#method_ba_ServerController__print_client_list">print_client_list()</a>, <a href="#method_ba_ServerController__shutdown">shutdown()</a></h5>
<dl>
<dt><h4><a name="method_ba_ServerController____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.ServerController(config: ServerConfig)</span></p>

</dd>
<dt><h4><a name="method_ba_ServerController__handle_transition">handle_transition()</a></dt></h4><dd>
<p><span>handle_transition(self) -&gt; bool</span></p>

<p>Handle transitioning to a new <a href="#class_ba_Session">ba.Session</a> or quitting the app.</p>

<p>Will be called once at the end of an activity that is marked as
a good 'end-point' (such as a final score screen).
Should return True if action will be handled by us; False if the
session should just continue on it's merry way.</p>

</dd>
<dt><h4><a name="method_ba_ServerController__kick">kick()</a></dt></h4><dd>
<p><span>kick(self, client_id: int, ban_time: Optional[int]) -&gt; None</span></p>

<p>Kick the provided client id.</p>

<p>ban_time is provided in seconds.
If ban_time is None, ban duration will be determined automatically.
Pass 0 or a negative number for no ban time.</p>

</dd>
<dt><h4><a name="method_ba_ServerController__print_client_list">print_client_list()</a></dt></h4><dd>
<p><span>print_client_list(self) -&gt; None</span></p>

<p>Print info about all connected clients.</p>

</dd>
<dt><h4><a name="method_ba_ServerController__shutdown">shutdown()</a></dt></h4><dd>
<p><span>shutdown(self, reason: ShutdownReason, immediate: bool) -&gt; None</span></p>

<p>Set the app to quit either now or at the next clean opportunity.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_Session">ba.Session</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Defines a high level series of <a href="#class_ba_Activity">ba.Activities</a> with a common purpose.</p>

<p>Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a></p>

<p>    Examples of sessions are <a href="#class_ba_FreeForAllSession">ba.FreeForAllSession</a>, <a href="#class_ba_DualTeamSession">ba.DualTeamSession</a>, and
    <a href="#class_ba_CoopSession">ba.CoopSession</a>.</p>

<p>    A Session is responsible for wrangling and transitioning between various
    <a href="#class_ba_Activity">ba.Activity</a> instances such as mini-games and score-screens, and for
    maintaining state between them (players, teams, score tallies, etc).</p>

<h3>Attributes:</h3>
<h5><a href="#attr_ba_Session__allow_mid_activity_joins">allow_mid_activity_joins</a>, <a href="#attr_ba_Session__customdata">customdata</a>, <a href="#attr_ba_Session__lobby">lobby</a>, <a href="#attr_ba_Session__max_players">max_players</a>, <a href="#attr_ba_Session__min_players">min_players</a>, <a href="#attr_ba_Session__sessionglobalsnode">sessionglobalsnode</a>, <a href="#attr_ba_Session__sessionplayers">sessionplayers</a>, <a href="#attr_ba_Session__sessionteams">sessionteams</a>, <a href="#attr_ba_Session__use_team_colors">use_team_colors</a>, <a href="#attr_ba_Session__use_teams">use_teams</a></h5>
<dl>
<dt><h4><a name="attr_ba_Session__allow_mid_activity_joins">allow_mid_activity_joins</a></h4></dt><dd>
<p><span>bool</span></p>
<p>Whether players should be allowed to join in the middle of
activities.</p>

</dd>
<dt><h4><a name="attr_ba_Session__customdata">customdata</a></h4></dt><dd>
<p><span>dict</span></p>
<p>A shared dictionary for objects to use as storage on this session.
Ensure that keys here are unique to avoid collisions.</p>

</dd>
<dt><h4><a name="attr_ba_Session__lobby">lobby</a></h4></dt><dd>
<p><span><a href="#class_ba_Lobby">ba.Lobby</a></span></p>
<p>The <a href="#class_ba_Lobby">ba.Lobby</a> instance where new <a href="#class_ba_Player">ba.Players</a> go to select a
Profile/Team/etc. before being added to games.
Be aware this value may be None if a Session does not allow
any such selection.</p>

</dd>
<dt><h4><a name="attr_ba_Session__max_players">max_players</a></h4></dt><dd>
<p><span>int</span></p>
<p>The maximum number of players allowed in the Session.</p>

</dd>
<dt><h4><a name="attr_ba_Session__min_players">min_players</a></h4></dt><dd>
<p><span>int</span></p>
<p>The minimum number of players who must be present for the Session
to proceed past the initial joining screen.</p>

</dd>
<dt><h4><a name="attr_ba_Session__sessionglobalsnode">sessionglobalsnode</a></h4></dt><dd>
<p><span><a href="#class_ba_Node">ba.Node</a></span></p>
<p>The sessionglobals <a href="#class_ba_Node">ba.Node</a> for the session.</p>

</dd>
<dt><h4><a name="attr_ba_Session__sessionplayers">sessionplayers</a></h4></dt><dd>
<p><span>List[<a href="#class_ba_SessionPlayer">ba.SessionPlayer</a>]</span></p>
<p>All <a href="#class_ba_SessionPlayer">ba.SessionPlayers</a> in the Session. Most things should use the
list of <a href="#class_ba_Player">ba.Players</a> in <a href="#class_ba_Activity">ba.Activity</a>; not this. Some players, such as
those who have not yet selected a character, will only be
found on this list.</p>

</dd>
<dt><h4><a name="attr_ba_Session__sessionteams">sessionteams</a></h4></dt><dd>
<p><span>List[<a href="#class_ba_SessionTeam">ba.SessionTeam</a>]</span></p>
<p>All the <a href="#class_ba_SessionTeam">ba.SessionTeams</a> in the Session. Most things should use the
list of <a href="#class_ba_Team">ba.Teams</a> in <a href="#class_ba_Activity">ba.Activity</a>; not this.</p>

</dd>
<dt><h4><a name="attr_ba_Session__use_team_colors">use_team_colors</a></h4></dt><dd>
<p><span>bool</span></p>
<p>Whether players on a team should all adopt the colors of that
team instead of their own profile colors. This only applies if
use_teams is enabled.</p>

</dd>
<dt><h4><a name="attr_ba_Session__use_teams">use_teams</a></h4></dt><dd>
<p><span>bool</span></p>
<p>Whether this session groups players into an explicit set of
teams. If this is off, a unique team is generated for each
player that joins.</p>

</dd>
</dl>
<h3>Methods:</h3>
<h5><a href="#method_ba_Session____init__">&lt;constructor&gt;</a>, <a href="#method_ba_Session__begin_next_activity">begin_next_activity()</a>, <a href="#method_ba_Session__end">end()</a>, <a href="#method_ba_Session__end_activity">end_activity()</a>, <a href="#method_ba_Session__get_custom_menu_entries">get_custom_menu_entries()</a>, <a href="#method_ba_Session__getactivity">getactivity()</a>, <a href="#method_ba_Session__handlemessage">handlemessage()</a>, <a href="#method_ba_Session__on_activity_end">on_activity_end()</a>, <a href="#method_ba_Session__on_player_leave">on_player_leave()</a>, <a href="#method_ba_Session__on_player_request">on_player_request()</a>, <a href="#method_ba_Session__on_team_join">on_team_join()</a>, <a href="#method_ba_Session__on_team_leave">on_team_leave()</a>, <a href="#method_ba_Session__setactivity">setactivity()</a></h5>
<dl>
<dt><h4><a name="method_ba_Session____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.Session(depsets: Sequence[<a href="#class_ba_DependencySet">ba.DependencySet</a>], team_names: Sequence[str] = None, team_colors: Sequence[Sequence[float]] = None, min_players: int = 1, max_players: int = 8)</span></p>

<p>Instantiate a session.</p>

<p>depsets should be a sequence of successfully resolved <a href="#class_ba_DependencySet">ba.DependencySet</a>
instances; one for each <a href="#class_ba_Activity">ba.Activity</a> the session may potentially run.</p>

</dd>
<dt><h4><a name="method_ba_Session__begin_next_activity">begin_next_activity()</a></dt></h4><dd>
<p><span>begin_next_activity(self) -&gt; None</span></p>

<p>Called once the previous activity has been totally torn down.</p>

<p>This means we're ready to begin the next one</p>

</dd>
<dt><h4><a name="method_ba_Session__end">end()</a></dt></h4><dd>
<p><span>end(self) -&gt; None</span></p>

<p>Initiates an end to the session and a return to the main menu.</p>

<p>Note that this happens asynchronously, allowing the
session and its activities to shut down gracefully.</p>

</dd>
<dt><h4><a name="method_ba_Session__end_activity">end_activity()</a></dt></h4><dd>
<p><span>end_activity(self, activity: <a href="#class_ba_Activity">ba.Activity</a>, results: Any, delay: float, force: bool) -&gt; None</span></p>

<p>Commence shutdown of a <a href="#class_ba_Activity">ba.Activity</a> (if not already occurring).</p>

<p>'delay' is the time delay before the Activity actually ends
(in seconds). Further calls to end() will be ignored up until
this time, unless 'force' is True, in which case the new results
will replace the old.</p>

</dd>
<dt><h4><a name="method_ba_Session__get_custom_menu_entries">get_custom_menu_entries()</a></dt></h4><dd>
<p><span>get_custom_menu_entries(self) -&gt; List[Dict[str, Any]]</span></p>

<p>Subclasses can override this to provide custom menu entries.</p>

<p>The returned value should be a list of dicts, each containing
a 'label' and 'call' entry, with 'label' being the text for
the entry and 'call' being the callable to trigger if the entry
is pressed.</p>

</dd>
<dt><h4><a name="method_ba_Session__getactivity">getactivity()</a></dt></h4><dd>
<p><span>getactivity(self) -&gt; Optional[<a href="#class_ba_Activity">ba.Activity</a>]</span></p>

<p>Return the current foreground activity for this session.</p>

</dd>
<dt><h4><a name="method_ba_Session__handlemessage">handlemessage()</a></dt></h4><dd>
<p><span>handlemessage(self, msg: Any) -&gt; Any</span></p>

<p>General message handling; can be passed any <a href="#class_category_Message_Classes">message object</a>.</p>

</dd>
<dt><h4><a name="method_ba_Session__on_activity_end">on_activity_end()</a></dt></h4><dd>
<p><span>on_activity_end(self, activity: <a href="#class_ba_Activity">ba.Activity</a>, results: Any) -&gt; None</span></p>

<p>Called when the current <a href="#class_ba_Activity">ba.Activity</a> has ended.</p>

<p>The <a href="#class_ba_Session">ba.Session</a> should look at the results and start
another <a href="#class_ba_Activity">ba.Activity</a>.</p>

</dd>
<dt><h4><a name="method_ba_Session__on_player_leave">on_player_leave()</a></dt></h4><dd>
<p><span>on_player_leave(self, sessionplayer: <a href="#class_ba_SessionPlayer">ba.SessionPlayer</a>) -&gt; None</span></p>

<p>Called when a previously-accepted <a href="#class_ba_SessionPlayer">ba.SessionPlayer</a> leaves.</p>

</dd>
<dt><h4><a name="method_ba_Session__on_player_request">on_player_request()</a></dt></h4><dd>
<p><span>on_player_request(self, player: <a href="#class_ba_SessionPlayer">ba.SessionPlayer</a>) -&gt; bool</span></p>

<p>Called when a new <a href="#class_ba_Player">ba.Player</a> wants to join the Session.</p>

<p>This should return True or False to accept/reject.</p>

</dd>
<dt><h4><a name="method_ba_Session__on_team_join">on_team_join()</a></dt></h4><dd>
<p><span>on_team_join(self, team: <a href="#class_ba_SessionTeam">ba.SessionTeam</a>) -&gt; None</span></p>

<p>Called when a new <a href="#class_ba_Team">ba.Team</a> joins the session.</p>

</dd>
<dt><h4><a name="method_ba_Session__on_team_leave">on_team_leave()</a></dt></h4><dd>
<p><span>on_team_leave(self, team: <a href="#class_ba_SessionTeam">ba.SessionTeam</a>) -&gt; None</span></p>

<p>Called when a <a href="#class_ba_Team">ba.Team</a> is leaving the session.</p>

</dd>
<dt><h4><a name="method_ba_Session__setactivity">setactivity()</a></dt></h4><dd>
<p><span>setactivity(self, activity: <a href="#class_ba_Activity">ba.Activity</a>) -&gt; None</span></p>

<p>Assign a new current <a href="#class_ba_Activity">ba.Activity</a> for the session.</p>

<p>Note that this will not change the current context to the new
Activity's. Code must be run in the new activity's methods
(on_transition_in, etc) to get it. (so you can't do
session.setactivity(foo) and then <a href="#function_ba_newnode">ba.newnode</a>() to add a node to foo)</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_SessionNotFoundError">ba.SessionNotFoundError</a></strong></h3>
<p>Inherits from: <a href="#class_ba_NotFoundError">ba.NotFoundError</a>, <a href="https://docs.python.org/3/library/exceptions.html#Exception">Exception</a>, <a href="https://docs.python.org/3/library/exceptions.html#BaseException">BaseException</a></p>
<p>Exception raised when an expected <a href="#class_ba_Session">ba.Session</a> does not exist.</p>

<p>Category: <a href="#class_category_Exception_Classes">Exception Classes</a>
</p>

<h3>Methods:</h3>
<p>&lt;all methods inherited from <a href="#class_ba_NotFoundError">ba.NotFoundError</a>&gt;</p>
<hr>
<h2><strong><a name="class_ba_SessionPlayer">ba.SessionPlayer</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>A reference to a player in the <a href="#class_ba_Session">ba.Session</a>.</p>

<p>Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a></p>

<p>These are created and managed internally and
provided to your Session/Activity instances.
Be aware that, like <a href="#class_ba_Node">ba.Nodes</a>, <a href="#class_ba_SessionPlayer">ba.SessionPlayer</a> objects are 'weak'
references under-the-hood; a player can leave the game at
 any point. For this reason, you should make judicious use of the
<a href="#method_ba_SessionPlayer__exists">ba.SessionPlayer.exists</a>() method (or boolean operator) to ensure
that a SessionPlayer is still present if retaining references to one
for any length of time.</p>

<h3>Attributes:</h3>
<h5><a href="#attr_ba_SessionPlayer__activityplayer">activityplayer</a>, <a href="#attr_ba_SessionPlayer__character">character</a>, <a href="#attr_ba_SessionPlayer__color">color</a>, <a href="#attr_ba_SessionPlayer__highlight">highlight</a>, <a href="#attr_ba_SessionPlayer__id">id</a>, <a href="#attr_ba_SessionPlayer__in_game">in_game</a>, <a href="#attr_ba_SessionPlayer__inputdevice">inputdevice</a>, <a href="#attr_ba_SessionPlayer__sessionteam">sessionteam</a></h5>
<dl>
<dt><h4><a name="attr_ba_SessionPlayer__activityplayer">activityplayer</a></h4></dt><dd>
<p><span> Optional[<a href="#class_ba_Player">ba.Player</a>]</span></p>
<p>The current game-specific instance for this player.</p>

</dd>
<dt><h4><a name="attr_ba_SessionPlayer__character">character</a></h4></dt><dd>
<p><span> str</span></p>
<p>The character this player has selected in their profile.</p>

</dd>
<dt><h4><a name="attr_ba_SessionPlayer__color">color</a></h4></dt><dd>
<p><span> Sequence[float]</span></p>
<p>The base color for this Player.
In team games this will match the <a href="#class_ba_SessionTeam">ba.SessionTeam</a>'s color.</p>

</dd>
<dt><h4><a name="attr_ba_SessionPlayer__highlight">highlight</a></h4></dt><dd>
<p><span> Sequence[float]</span></p>
<p>A secondary color for this player.
This is used for minor highlights and accents
to allow a player to stand apart from his teammates
who may all share the same team (primary) color.</p>

</dd>
<dt><h4><a name="attr_ba_SessionPlayer__id">id</a></h4></dt><dd>
<p><span> int</span></p>
<p>The unique numeric ID of the Player.</p>

<p>Note that you can also use the boolean operator for this same
functionality, so a statement such as "if player" will do
the right thing both for Player objects and values of None.</p>

</dd>
<dt><h4><a name="attr_ba_SessionPlayer__in_game">in_game</a></h4></dt><dd>
<p><span> bool</span></p>
<p>This bool value will be True once the Player has completed
any lobby character/team selection.</p>

</dd>
<dt><h4><a name="attr_ba_SessionPlayer__inputdevice">inputdevice</a></h4></dt><dd>
<p><span> <a href="#class_ba_InputDevice">ba.InputDevice</a></span></p>
<p>The input device associated with the player.</p>

</dd>
<dt><h4><a name="attr_ba_SessionPlayer__sessionteam">sessionteam</a></h4></dt><dd>
<p><span> <a href="#class_ba_SessionTeam">ba.SessionTeam</a></span></p>
<p>The <a href="#class_ba_SessionTeam">ba.SessionTeam</a> this Player is on. If the SessionPlayer
is still in its lobby selecting a team/etc. then a
<a href="#class_ba_SessionTeamNotFoundError">ba.SessionTeamNotFoundError</a> will be raised.</p>

</dd>
</dl>
<h3>Methods:</h3>
<h5><a href="#method_ba_SessionPlayer__assigninput">assigninput()</a>, <a href="#method_ba_SessionPlayer__exists">exists()</a>, <a href="#method_ba_SessionPlayer__get_account_id">get_account_id()</a>, <a href="#method_ba_SessionPlayer__get_icon">get_icon()</a>, <a href="#method_ba_SessionPlayer__getname">getname()</a>, <a href="#method_ba_SessionPlayer__remove_from_game">remove_from_game()</a>, <a href="#method_ba_SessionPlayer__resetinput">resetinput()</a>, <a href="#method_ba_SessionPlayer__setname">setname()</a></h5>
<dl>
<dt><h4><a name="method_ba_SessionPlayer__assigninput">assigninput()</a></dt></h4><dd>
<p><span>assigninput(type: Union[<a href="#class_ba_InputType">ba.InputType</a>, Tuple[<a href="#class_ba_InputType">ba.InputType</a>, ...]],
  call: Callable) -&gt; None</span></p>

<p>Set the python callable to be run for one or more types of input.</p>

</dd>
<dt><h4><a name="method_ba_SessionPlayer__exists">exists()</a></dt></h4><dd>
<p><span>exists() -&gt; bool</span></p>

<p>Return whether the underlying player is still in the game.</p>

</dd>
<dt><h4><a name="method_ba_SessionPlayer__get_account_id">get_account_id()</a></dt></h4><dd>
<p><span>get_account_id() -&gt; str</span></p>

<p>Return the Account ID this player is signed in under, if
there is one and it can be determined with relative certainty.
Returns None otherwise. Note that this may require an active
internet connection (especially for network-connected players)
and may return None for a short while after a player initially
joins (while verification occurs).</p>

</dd>
<dt><h4><a name="method_ba_SessionPlayer__get_icon">get_icon()</a></dt></h4><dd>
<p><span>get_icon() -&gt; Dict[str, Any]</span></p>

<p>Returns the character's icon (images, colors, etc contained in a dict)</p>

</dd>
<dt><h4><a name="method_ba_SessionPlayer__getname">getname()</a></dt></h4><dd>
<p><span>getname(full: bool = False, icon: bool = True) -&gt; str</span></p>

<p>Returns the player's name. If icon is True, the long version of the
name may include an icon.</p>

</dd>
<dt><h4><a name="method_ba_SessionPlayer__remove_from_game">remove_from_game()</a></dt></h4><dd>
<p><span>remove_from_game() -&gt; None</span></p>

<p>Removes the player from the game.</p>

</dd>
<dt><h4><a name="method_ba_SessionPlayer__resetinput">resetinput()</a></dt></h4><dd>
<p><span>resetinput() -&gt; None</span></p>

<p>Clears out the player's assigned input actions.</p>

</dd>
<dt><h4><a name="method_ba_SessionPlayer__setname">setname()</a></dt></h4><dd>
<p><span>setname(name: str, full_name: str = None, real: bool = True)
  -&gt; None</span></p>

<p>Set the player's name to the provided string.
A number will automatically be appended if the name is not unique from
other players.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_SessionPlayerNotFoundError">ba.SessionPlayerNotFoundError</a></strong></h3>
<p>Inherits from: <a href="#class_ba_NotFoundError">ba.NotFoundError</a>, <a href="https://docs.python.org/3/library/exceptions.html#Exception">Exception</a>, <a href="https://docs.python.org/3/library/exceptions.html#BaseException">BaseException</a></p>
<p>Exception raised when an expected <a href="#class_ba_SessionPlayer">ba.SessionPlayer</a> does not exist.</p>

<p>Category: <a href="#class_category_Exception_Classes">Exception Classes</a>
</p>

<h3>Methods:</h3>
<p>&lt;all methods inherited from <a href="#class_ba_NotFoundError">ba.NotFoundError</a>&gt;</p>
<hr>
<h2><strong><a name="class_ba_SessionTeam">ba.SessionTeam</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>A team of one or more <a href="#class_ba_SessionPlayer">ba.SessionPlayers</a>.</p>

<p>Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a></p>

<p>    Note that a SessionPlayer *always* has a SessionTeam;
    in some cases, such as free-for-all <a href="#class_ba_Session">ba.Sessions</a>,
    each SessionTeam consists of just one SessionPlayer.</p>

<h3>Attributes:</h3>
<h5><a href="#attr_ba_SessionTeam__color">color</a>, <a href="#attr_ba_SessionTeam__customdata">customdata</a>, <a href="#attr_ba_SessionTeam__id">id</a>, <a href="#attr_ba_SessionTeam__name">name</a>, <a href="#attr_ba_SessionTeam__players">players</a></h5>
<dl>
<dt><h4><a name="attr_ba_SessionTeam__color">color</a></h4></dt><dd>
<p><span>Tuple[float, ...]</span></p>
<p>The team's color.</p>

</dd>
<dt><h4><a name="attr_ba_SessionTeam__customdata">customdata</a></h4></dt><dd>
<p><span>dict</span></p>
<p>A dict for use by the current <a href="#class_ba_Session">ba.Session</a> for
storing data associated with this team.
Unlike customdata, this persists for the duration
of the session.</p>

</dd>
<dt><h4><a name="attr_ba_SessionTeam__id">id</a></h4></dt><dd>
<p><span>int</span></p>
<p>The unique numeric id of the team.</p>

</dd>
<dt><h4><a name="attr_ba_SessionTeam__name">name</a></h4></dt><dd>
<p><span>Union[<a href="#class_ba_Lstr">ba.Lstr</a>, str]</span></p>
<p>The team's name.</p>

</dd>
<dt><h4><a name="attr_ba_SessionTeam__players">players</a></h4></dt><dd>
<p><span>List[<a href="#class_ba_SessionPlayer">ba.SessionPlayer</a>]</span></p>
<p>The list of <a href="#class_ba_SessionPlayer">ba.SessionPlayers</a> on the team.</p>

</dd>
</dl>
<h3>Methods:</h3>
<dl>
<dt><h4><a name="method_ba_SessionTeam____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.SessionTeam(team_id: 'int' = 0, name: 'Union[<a href="#class_ba_Lstr">ba.Lstr</a>, str]' = '', color: 'Sequence[float]' = (1.0, 1.0, 1.0))</span></p>

<p>Instantiate a ba.SessionTeam.</p>

<p>In most cases, all teams are provided to you by the <a href="#class_ba_Session">ba.Session</a>,
<a href="#class_ba_Session">ba.Session</a>, so calling this shouldn't be necessary.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_SessionTeamNotFoundError">ba.SessionTeamNotFoundError</a></strong></h3>
<p>Inherits from: <a href="#class_ba_NotFoundError">ba.NotFoundError</a>, <a href="https://docs.python.org/3/library/exceptions.html#Exception">Exception</a>, <a href="https://docs.python.org/3/library/exceptions.html#BaseException">BaseException</a></p>
<p>Exception raised when an expected <a href="#class_ba_SessionTeam">ba.SessionTeam</a> does not exist.</p>

<p>Category: <a href="#class_category_Exception_Classes">Exception Classes</a>
</p>

<h3>Methods:</h3>
<p>&lt;all methods inherited from <a href="#class_ba_NotFoundError">ba.NotFoundError</a>&gt;</p>
<hr>
<h2><strong><a name="class_ba_Setting">ba.Setting</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Defines a user-controllable setting for a game or other entity.</p>

<p>Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a>
</p>

<h3>Methods:</h3>
<dl>
<dt><h4><a name="method_ba_Setting____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.Setting(name: str, default: Any)</span></p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_ShouldShatterMessage">ba.ShouldShatterMessage</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Tells an object that it should shatter.</p>

<p>Category: <a href="#class_category_Message_Classes">Message Classes</a>
</p>

<h3>Methods:</h3>
<dl>
<dt><h4><a name="method_ba_ShouldShatterMessage____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.ShouldShatterMessage()</span></p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_Sound">ba.Sound</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>A reference to a sound.</p>

<p>Category: <a href="#class_category_Asset_Classes">Asset Classes</a></p>

<p>Use <a href="#function_ba_getsound">ba.getsound</a>() to instantiate one.</p>

<hr>
<h2><strong><a name="class_ba_SpecialChar">ba.SpecialChar</a></strong></h3>
<p>Inherits from: <a href="https://docs.python.org/3/library/enum.html#enum.Enum">enum.Enum</a></p>
<p>Special characters the game can print.</p>

<p>Category: <a href="#class_category_Enums">Enums</a>
</p>

<h3>Values:</h3>
<ul>
<li>DOWN_ARROW</li>
<li>UP_ARROW</li>
<li>LEFT_ARROW</li>
<li>RIGHT_ARROW</li>
<li>TOP_BUTTON</li>
<li>LEFT_BUTTON</li>
<li>RIGHT_BUTTON</li>
<li>BOTTOM_BUTTON</li>
<li>DELETE</li>
<li>SHIFT</li>
<li>BACK</li>
<li>LOGO_FLAT</li>
<li>REWIND_BUTTON</li>
<li>PLAY_PAUSE_BUTTON</li>
<li>FAST_FORWARD_BUTTON</li>
<li>DPAD_CENTER_BUTTON</li>
<li>OUYA_BUTTON_O</li>
<li>OUYA_BUTTON_U</li>
<li>OUYA_BUTTON_Y</li>
<li>OUYA_BUTTON_A</li>
<li>OUYA_LOGO</li>
<li>LOGO</li>
<li>TICKET</li>
<li>GOOGLE_PLAY_GAMES_LOGO</li>
<li>GAME_CENTER_LOGO</li>
<li>DICE_BUTTON1</li>
<li>DICE_BUTTON2</li>
<li>DICE_BUTTON3</li>
<li>DICE_BUTTON4</li>
<li>GAME_CIRCLE_LOGO</li>
<li>PARTY_ICON</li>
<li>TEST_ACCOUNT</li>
<li>TICKET_BACKING</li>
<li>TROPHY1</li>
<li>TROPHY2</li>
<li>TROPHY3</li>
<li>TROPHY0A</li>
<li>TROPHY0B</li>
<li>TROPHY4</li>
<li>LOCAL_ACCOUNT</li>
<li>ALIBABA_LOGO</li>
<li>FLAG_UNITED_STATES</li>
<li>FLAG_MEXICO</li>
<li>FLAG_GERMANY</li>
<li>FLAG_BRAZIL</li>
<li>FLAG_RUSSIA</li>
<li>FLAG_CHINA</li>
<li>FLAG_UNITED_KINGDOM</li>
<li>FLAG_CANADA</li>
<li>FLAG_INDIA</li>
<li>FLAG_JAPAN</li>
<li>FLAG_FRANCE</li>
<li>FLAG_INDONESIA</li>
<li>FLAG_ITALY</li>
<li>FLAG_SOUTH_KOREA</li>
<li>FLAG_NETHERLANDS</li>
<li>FEDORA</li>
<li>HAL</li>
<li>CROWN</li>
<li>YIN_YANG</li>
<li>EYE_BALL</li>
<li>SKULL</li>
<li>HEART</li>
<li>DRAGON</li>
<li>HELMET</li>
<li>MUSHROOM</li>
<li>NINJA_STAR</li>
<li>VIKING_HELMET</li>
<li>MOON</li>
<li>SPIDER</li>
<li>FIREBALL</li>
<li>FLAG_UNITED_ARAB_EMIRATES</li>
<li>FLAG_QATAR</li>
<li>FLAG_EGYPT</li>
<li>FLAG_KUWAIT</li>
<li>FLAG_ALGERIA</li>
<li>FLAG_SAUDI_ARABIA</li>
<li>FLAG_MALAYSIA</li>
<li>FLAG_CZECH_REPUBLIC</li>
<li>FLAG_AUSTRALIA</li>
<li>FLAG_SINGAPORE</li>
<li>OCULUS_LOGO</li>
<li>STEAM_LOGO</li>
<li>NVIDIA_LOGO</li>
<li>FLAG_IRAN</li>
<li>FLAG_POLAND</li>
<li>FLAG_ARGENTINA</li>
<li>FLAG_PHILIPPINES</li>
<li>FLAG_CHILE</li>
<li>MIKIROG</li>
</ul>
<hr>
<h2><strong><a name="class_ba_StandLocation">ba.StandLocation</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Describes a point in space and an angle to face.</p>

<p>Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a>
</p>

<h3>Methods:</h3>
<dl>
<dt><h4><a name="method_ba_StandLocation____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.StandLocation(position: <a href="#class_ba_Vec3">ba.Vec3</a>, angle: Optional[float] = None)</span></p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_StandMessage">ba.StandMessage</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>A message telling an object to move to a position in space.</p>

<p>Category: <a href="#class_category_Message_Classes">Message Classes</a></p>

<p>    Used when teleporting players to home base, etc.</p>

<h3>Attributes:</h3>
<h5><a href="#attr_ba_StandMessage__angle">angle</a>, <a href="#attr_ba_StandMessage__position">position</a></h5>
<dl>
<dt><h4><a name="attr_ba_StandMessage__angle">angle</a></h4></dt><dd>
<p><span>float</span></p>
<p>The angle to face (in degrees)</p>

</dd>
<dt><h4><a name="attr_ba_StandMessage__position">position</a></h4></dt><dd>
<p><span>Sequence[float]</span></p>
<p>Where to move to.</p>

</dd>
</dl>
<h3>Methods:</h3>
<dl>
<dt><h4><a name="method_ba_StandMessage____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.StandMessage(position: Sequence[float] = (0.0, 0.0, 0.0), angle: float = 0.0)</span></p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_Stats">ba.Stats</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Manages scores and statistics for a <a href="#class_ba_Session">ba.Session</a>.</p>

<p>Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a>
</p>

<h3>Methods:</h3>
<h5><a href="#method_ba_Stats____init__">&lt;constructor&gt;</a>, <a href="#method_ba_Stats__get_records">get_records()</a>, <a href="#method_ba_Stats__getactivity">getactivity()</a>, <a href="#method_ba_Stats__player_scored">player_scored()</a>, <a href="#method_ba_Stats__player_was_killed">player_was_killed()</a>, <a href="#method_ba_Stats__register_sessionplayer">register_sessionplayer()</a>, <a href="#method_ba_Stats__reset">reset()</a>, <a href="#method_ba_Stats__reset_accum">reset_accum()</a>, <a href="#method_ba_Stats__setactivity">setactivity()</a></h5>
<dl>
<dt><h4><a name="method_ba_Stats____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.Stats()</span></p>

</dd>
<dt><h4><a name="method_ba_Stats__get_records">get_records()</a></dt></h4><dd>
<p><span>get_records(self) -&gt; Dict[str, <a href="#class_ba_PlayerRecord">ba.PlayerRecord</a>]</span></p>

<p>Get PlayerRecord corresponding to still-existing players.</p>

</dd>
<dt><h4><a name="method_ba_Stats__getactivity">getactivity()</a></dt></h4><dd>
<p><span>getactivity(self) -&gt; Optional[<a href="#class_ba_Activity">ba.Activity</a>]</span></p>

<p>Get the activity associated with this instance.</p>

<p>May return None.</p>

</dd>
<dt><h4><a name="method_ba_Stats__player_scored">player_scored()</a></dt></h4><dd>
<p><span>player_scored(self, player: <a href="#class_ba_Player">ba.Player</a>, base_points: int = 1, target: Sequence[float] = None, kill: bool = False, victim_player: <a href="#class_ba_Player">ba.Player</a> = None, scale: float = 1.0, color: Sequence[float] = None, title: Union[str, <a href="#class_ba_Lstr">ba.Lstr</a>] = None, screenmessage: bool = True, display: bool = True, importance: int = 1, showpoints: bool = True, big_message: bool = False) -&gt; int</span></p>

<p>Register a score for the player.</p>

<p>Return value is actual score with multipliers and such factored in.</p>

</dd>
<dt><h4><a name="method_ba_Stats__player_was_killed">player_was_killed()</a></dt></h4><dd>
<p><span>player_was_killed(self, player: <a href="#class_ba_Player">ba.Player</a>, killed: bool = False, killer: <a href="#class_ba_Player">ba.Player</a> = None) -&gt; None</span></p>

<p>Should be called when a player is killed.</p>

</dd>
<dt><h4><a name="method_ba_Stats__register_sessionplayer">register_sessionplayer()</a></dt></h4><dd>
<p><span>register_sessionplayer(self, player: <a href="#class_ba_SessionPlayer">ba.SessionPlayer</a>) -&gt; None</span></p>

<p>Register a <a href="#class_ba_SessionPlayer">ba.SessionPlayer</a> with this score-set.</p>

</dd>
<dt><h4><a name="method_ba_Stats__reset">reset()</a></dt></h4><dd>
<p><span>reset(self) -&gt; None</span></p>

<p>Reset the stats instance completely.</p>

</dd>
<dt><h4><a name="method_ba_Stats__reset_accum">reset_accum()</a></dt></h4><dd>
<p><span>reset_accum(self) -&gt; None</span></p>

<p>Reset per-sound sub-scores.</p>

</dd>
<dt><h4><a name="method_ba_Stats__setactivity">setactivity()</a></dt></h4><dd>
<p><span>setactivity(self, activity: Optional[<a href="#class_ba_Activity">ba.Activity</a>]) -&gt; None</span></p>

<p>Set the current activity for this instance.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_Team">ba.Team</a></strong></h3>
<p>Inherits from: <a href="https://docs.python.org/3/library/typing.html#typing.Generic">typing.Generic</a></p>
<p>A team in a specific <a href="#class_ba_Activity">ba.Activity</a>.</p>

<p>Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a></p>

<p>    These correspond to <a href="#class_ba_SessionTeam">ba.SessionTeam</a> objects, but are created per activity
    so that the activity can use its own custom team subclass.
</p>

<h3>Attributes:</h3>
<h5><a href="#attr_ba_Team__customdata">customdata</a>, <a href="#attr_ba_Team__sessionteam">sessionteam</a></h5>
<dl>
<dt><h4><a name="attr_ba_Team__customdata">customdata</a></h4></dt><dd>
<p><span>dict</span></p>
<p>Arbitrary values associated with the team.
        Though it is encouraged that most player values be properly defined
        on the <a href="#class_ba_Team">ba.Team</a> subclass, it may be useful for player-agnostic
        objects to store values here. This dict is cleared when the team
        leaves or expires so objects stored here will be disposed of at
        the expected time, unlike the Team instance itself which may
        continue to be referenced after it is no longer part of the game.</p>

</dd>
<dt><h4><a name="attr_ba_Team__sessionteam">sessionteam</a></h4></dt><dd>
<p><span>SessionTeam</span></p>
<p>Return the <a href="#class_ba_SessionTeam">ba.SessionTeam</a> corresponding to this Team.</p>

<p>        Throws a <a href="#class_ba_SessionTeamNotFoundError">ba.SessionTeamNotFoundError</a> if there is none.</p>

</dd>
</dl>
<h3>Methods:</h3>
<h5><a href="#method_ba_Team__manual_init">manual_init()</a>, <a href="#method_ba_Team__on_expire">on_expire()</a></h5>
<dl>
<dt><h4><a name="method_ba_Team__manual_init">manual_init()</a></dt></h4><dd>
<p><span>manual_init(self, team_id: int, name: Union[<a href="#class_ba_Lstr">ba.Lstr</a>, str], color: Tuple[float, ...]) -&gt; None</span></p>

<p>Manually init a team for uses such as bots.</p>

</dd>
<dt><h4><a name="method_ba_Team__on_expire">on_expire()</a></dt></h4><dd>
<p><span>on_expire(self) -&gt; None</span></p>

<p>Can be overridden to handle team expiration.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_TeamGameActivity">ba.TeamGameActivity</a></strong></h3>
<p>Inherits from: <a href="#class_ba_GameActivity">ba.GameActivity</a>, <a href="#class_ba_Activity">ba.Activity</a>, <a href="#class_ba_DependencyComponent">ba.DependencyComponent</a>, <a href="https://docs.python.org/3/library/typing.html#typing.Generic">typing.Generic</a></p>
<p>Base class for teams and free-for-all mode games.</p>

<p>Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a></p>

<p>    (Free-for-all is essentially just a special case where every
    <a href="#class_ba_Player">ba.Player</a> has their own <a href="#class_ba_Team">ba.Team</a>)
</p>

<h3>Attributes Inherited:</h3>
<h5><a href="#attr_ba_Activity__players">players</a>, <a href="#attr_ba_Activity__settings_raw">settings_raw</a>, <a href="#attr_ba_Activity__teams">teams</a></h5>
<h3>Attributes Defined Here:</h3>
<h5><a href="#attr_ba_TeamGameActivity__customdata">customdata</a>, <a href="#attr_ba_TeamGameActivity__expired">expired</a>, <a href="#attr_ba_TeamGameActivity__globalsnode">globalsnode</a>, <a href="#attr_ba_TeamGameActivity__map">map</a>, <a href="#attr_ba_TeamGameActivity__playertype">playertype</a>, <a href="#attr_ba_TeamGameActivity__session">session</a>, <a href="#attr_ba_TeamGameActivity__stats">stats</a>, <a href="#attr_ba_TeamGameActivity__teamtype">teamtype</a></h5>
<dl>
<dt><h4><a name="attr_ba_TeamGameActivity__customdata">customdata</a></h4></dt><dd>
<p><span>dict</span></p>
<p>Entities needing to store simple data with an activity can put it
        here. This dict will be deleted when the activity expires, so contained
        objects generally do not need to worry about handling expired
        activities.</p>

</dd>
<dt><h4><a name="attr_ba_TeamGameActivity__expired">expired</a></h4></dt><dd>
<p><span>bool</span></p>
<p>Whether the activity is expired.</p>

<p>        An activity is set as expired when shutting down.
        At this point no new nodes, timers, etc should be made,
        run, etc, and the activity should be considered a 'zombie'.</p>

</dd>
<dt><h4><a name="attr_ba_TeamGameActivity__globalsnode">globalsnode</a></h4></dt><dd>
<p><span><a href="#class_ba_Node">ba.Node</a></span></p>
<p>The 'globals' <a href="#class_ba_Node">ba.Node</a> for the activity. This contains various
        global controls and values.</p>

</dd>
<dt><h4><a name="attr_ba_TeamGameActivity__map">map</a></h4></dt><dd>
<p><span><a href="#class_ba_Map">ba.Map</a></span></p>
<p>The map being used for this game.</p>

<p>        Raises a <a href="#class_ba_NotFoundError">ba.NotFoundError</a> if the map does not currently exist.</p>

</dd>
<dt><h4><a name="attr_ba_TeamGameActivity__playertype">playertype</a></h4></dt><dd>
<p><span>Type[PlayerType]</span></p>
<p>The type of <a href="#class_ba_Player">ba.Player</a> this Activity is using.</p>

</dd>
<dt><h4><a name="attr_ba_TeamGameActivity__session">session</a></h4></dt><dd>
<p><span><a href="#class_ba_Session">ba.Session</a></span></p>
<p>The <a href="#class_ba_Session">ba.Session</a> this <a href="#class_ba_Activity">ba.Activity</a> belongs go.</p>

<p>        Raises a <a href="#class_ba_SessionNotFoundError">ba.SessionNotFoundError</a> if the Session no longer exists.</p>

</dd>
<dt><h4><a name="attr_ba_TeamGameActivity__stats">stats</a></h4></dt><dd>
<p><span><a href="#class_ba_Stats">ba.Stats</a></span></p>
<p>The stats instance accessible while the activity is running.</p>

<p>        If access is attempted before or after, raises a <a href="#class_ba_NotFoundError">ba.NotFoundError</a>.</p>

</dd>
<dt><h4><a name="attr_ba_TeamGameActivity__teamtype">teamtype</a></h4></dt><dd>
<p><span>Type[TeamType]</span></p>
<p>The type of <a href="#class_ba_Team">ba.Team</a> this Activity is using.</p>

</dd>
</dl>
<h3>Methods Inherited:</h3>
<h5><a href="#method_ba_GameActivity__add_actor_weak_ref">add_actor_weak_ref()</a>, <a href="#method_ba_GameActivity__add_player">add_player()</a>, <a href="#method_ba_GameActivity__add_team">add_team()</a>, <a href="#method_ba_GameActivity__begin">begin()</a>, <a href="#method_ba_GameActivity__continue_or_end_game">continue_or_end_game()</a>, <a href="#method_ba_GameActivity__create_player">create_player()</a>, <a href="#method_ba_GameActivity__create_settings_ui">create_settings_ui()</a>, <a href="#method_ba_GameActivity__create_team">create_team()</a>, <a href="#method_ba_GameActivity__dep_is_present">dep_is_present()</a>, <a href="#method_ba_GameActivity__end_game">end_game()</a>, <a href="#method_ba_GameActivity__expire">expire()</a>, <a href="#method_ba_GameActivity__get_available_settings">get_available_settings()</a>, <a href="#method_ba_GameActivity__get_description">get_description()</a>, <a href="#method_ba_GameActivity__get_description_display_string">get_description_display_string()</a>, <a href="#method_ba_GameActivity__get_display_string">get_display_string()</a>, <a href="#method_ba_GameActivity__get_dynamic_deps">get_dynamic_deps()</a>, <a href="#method_ba_GameActivity__get_instance_description">get_instance_description()</a>, <a href="#method_ba_GameActivity__get_instance_description_short">get_instance_description_short()</a>, <a href="#method_ba_GameActivity__get_instance_display_string">get_instance_display_string()</a>, <a href="#method_ba_GameActivity__get_instance_scoreboard_display_string">get_instance_scoreboard_display_string()</a>, <a href="#method_ba_GameActivity__get_settings_display_string">get_settings_display_string()</a>, <a href="#method_ba_GameActivity__get_supported_maps">get_supported_maps()</a>, <a href="#method_ba_GameActivity__get_team_display_string">get_team_display_string()</a>, <a href="#method_ba_GameActivity__getname">getname()</a>, <a href="#method_ba_GameActivity__getscoreconfig">getscoreconfig()</a>, <a href="#method_ba_GameActivity__handlemessage">handlemessage()</a>, <a href="#method_ba_GameActivity__has_begun">has_begun()</a>, <a href="#method_ba_GameActivity__has_ended">has_ended()</a>, <a href="#method_ba_GameActivity__has_transitioned_in">has_transitioned_in()</a>, <a href="#method_ba_GameActivity__is_transitioning_out">is_transitioning_out()</a>, <a href="#method_ba_GameActivity__is_waiting_for_continue">is_waiting_for_continue()</a>, <a href="#method_ba_GameActivity__on_continue">on_continue()</a>, <a href="#method_ba_GameActivity__on_expire">on_expire()</a>, <a href="#method_ba_GameActivity__on_player_join">on_player_join()</a>, <a href="#method_ba_GameActivity__on_player_leave">on_player_leave()</a>, <a href="#method_ba_GameActivity__on_team_join">on_team_join()</a>, <a href="#method_ba_GameActivity__on_team_leave">on_team_leave()</a>, <a href="#method_ba_GameActivity__on_transition_out">on_transition_out()</a>, <a href="#method_ba_GameActivity__remove_player">remove_player()</a>, <a href="#method_ba_GameActivity__remove_team">remove_team()</a>, <a href="#method_ba_GameActivity__respawn_player">respawn_player()</a>, <a href="#method_ba_GameActivity__retain_actor">retain_actor()</a>, <a href="#method_ba_GameActivity__set_has_ended">set_has_ended()</a>, <a href="#method_ba_GameActivity__setup_standard_powerup_drops">setup_standard_powerup_drops()</a>, <a href="#method_ba_GameActivity__setup_standard_time_limit">setup_standard_time_limit()</a>, <a href="#method_ba_GameActivity__show_zoom_message">show_zoom_message()</a>, <a href="#method_ba_GameActivity__spawn_player">spawn_player()</a>, <a href="#method_ba_GameActivity__spawn_player_if_exists">spawn_player_if_exists()</a>, <a href="#method_ba_GameActivity__transition_in">transition_in()</a>, <a href="#method_ba_GameActivity__transition_out">transition_out()</a></h5>
<h3>Methods Defined or Overridden:</h3>
<h5><a href="#method_ba_TeamGameActivity____init__">&lt;constructor&gt;</a>, <a href="#method_ba_TeamGameActivity__end">end()</a>, <a href="#method_ba_TeamGameActivity__on_begin">on_begin()</a>, <a href="#method_ba_TeamGameActivity__on_transition_in">on_transition_in()</a>, <a href="#method_ba_TeamGameActivity__spawn_player_spaz">spawn_player_spaz()</a>, <a href="#method_ba_TeamGameActivity__supports_session_type">supports_session_type()</a></h5>
<dl>
<dt><h4><a name="method_ba_TeamGameActivity____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.TeamGameActivity(settings: dict)</span></p>

<p>Instantiate the Activity.</p>

</dd>
<dt><h4><a name="method_ba_TeamGameActivity__end">end()</a></dt></h4><dd>
<p><span>end(self, results: Any = None, announce_winning_team: bool = True, announce_delay: float = 0.1, force: bool = False) -&gt; None</span></p>

<p>End the game and announce the single winning team
unless 'announce_winning_team' is False.
(for results without a single most-important winner).</p>

</dd>
<dt><h4><a name="method_ba_TeamGameActivity__on_begin">on_begin()</a></dt></h4><dd>
<p><span>on_begin(self) -&gt; None</span></p>

<p>Called once the previous <a href="#class_ba_Activity">ba.Activity</a> has finished transitioning out.</p>

<p>At this point the activity's initial players and teams are filled in
and it should begin its actual game logic.</p>

</dd>
<dt><h4><a name="method_ba_TeamGameActivity__on_transition_in">on_transition_in()</a></dt></h4><dd>
<p><span>on_transition_in(self) -&gt; None</span></p>

<p>Called when the Activity is first becoming visible.</p>

<p>Upon this call, the Activity should fade in backgrounds,
start playing music, etc. It does not yet have access to players
or teams, however. They remain owned by the previous Activity
up until <a href="#method_ba_Activity__on_begin">ba.Activity.on_begin</a>() is called.</p>

</dd>
<dt><h4><a name="method_ba_TeamGameActivity__spawn_player_spaz">spawn_player_spaz()</a></dt></h4><dd>
<p><span>spawn_player_spaz(self, player: PlayerType, position: Sequence[float] = None, angle: float = None) -&gt; PlayerSpaz</span></p>

<p>Method override; spawns and wires up a standard ba.PlayerSpaz for
a <a href="#class_ba_Player">ba.Player</a>.</p>

<p>If position or angle is not supplied, a default will be chosen based
on the <a href="#class_ba_Player">ba.Player</a> and their <a href="#class_ba_Team">ba.Team</a>.</p>

</dd>
<dt><h4><a name="method_ba_TeamGameActivity__supports_session_type">supports_session_type()</a></dt></h4><dd>
<h5><span><em>&lt;class method&gt;</span></em></h5>
<p><span>supports_session_type(sessiontype: Type[<a href="#class_ba_Session">ba.Session</a>]) -&gt; bool </span></p>

<p>Class method override;
returns True for <a href="#class_ba_DualTeamSession">ba.DualTeamSessions</a> and <a href="#class_ba_FreeForAllSession">ba.FreeForAllSessions</a>;
False otherwise.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_TeamNotFoundError">ba.TeamNotFoundError</a></strong></h3>
<p>Inherits from: <a href="#class_ba_NotFoundError">ba.NotFoundError</a>, <a href="https://docs.python.org/3/library/exceptions.html#Exception">Exception</a>, <a href="https://docs.python.org/3/library/exceptions.html#BaseException">BaseException</a></p>
<p>Exception raised when an expected <a href="#class_ba_Team">ba.Team</a> does not exist.</p>

<p>Category: <a href="#class_category_Exception_Classes">Exception Classes</a>
</p>

<h3>Methods:</h3>
<p>&lt;all methods inherited from <a href="#class_ba_NotFoundError">ba.NotFoundError</a>&gt;</p>
<hr>
<h2><strong><a name="class_ba_Texture">ba.Texture</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>A reference to a texture.</p>

<p>Category: <a href="#class_category_Asset_Classes">Asset Classes</a></p>

<p>Use <a href="#function_ba_gettexture">ba.gettexture</a>() to instantiate one.</p>

<hr>
<h2><strong><a name="class_ba_ThawMessage">ba.ThawMessage</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Tells an object to stop being frozen.</p>

<p>Category: <a href="#class_category_Message_Classes">Message Classes</a>
</p>

<h3>Methods:</h3>
<dl>
<dt><h4><a name="method_ba_ThawMessage____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.ThawMessage()</span></p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_TimeFormat">ba.TimeFormat</a></strong></h3>
<p>Inherits from: <a href="https://docs.python.org/3/library/enum.html#enum.Enum">enum.Enum</a></p>
<p>Specifies the format time values are provided in.</p>

<p>Category: <a href="#class_category_Enums">Enums</a>
</p>

<h3>Values:</h3>
<ul>
<li>SECONDS</li>
<li>MILLISECONDS</li>
</ul>
<hr>
<h2><strong><a name="class_ba_Timer">ba.Timer</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Timer(time: float, call: Callable[[], Any], repeat: bool = False,
  timetype: <a href="#class_ba_TimeType">ba.TimeType</a> = TimeType.SIM,
  timeformat: <a href="#class_ba_TimeFormat">ba.TimeFormat</a> = TimeFormat.SECONDS,
  suppress_format_warning: bool = False)</p>

<p>Timers are used to run code at later points in time.</p>

<p>Category: <a href="#class_category_General_Utility_Classes">General Utility Classes</a></p>

<p>This class encapsulates a timer in the current <a href="#class_ba_Context">ba.Context</a>.
The underlying timer will be destroyed when either this object is
no longer referenced or when its Context (Activity, etc.) dies. If you
do not want to worry about keeping a reference to your timer around,
you should use the <a href="#function_ba_timer">ba.timer</a>() function instead.</p>

<p>time: length of time (in seconds by default) that the timer will wait
before firing. Note that the actual delay experienced may vary
depending on the timetype. (see below)</p>

<p>call: A callable Python object. Note that the timer will retain a
strong reference to the callable for as long as it exists, so you
may want to look into concepts such as <a href="#class_ba_WeakCall">ba.WeakCall</a> if that is not
desired.</p>

<p>repeat: if True, the timer will fire repeatedly, with each successive
firing having the same delay as the first.</p>

<p>timetype: A <a href="#class_ba_TimeType">ba.TimeType</a> value determining which timeline the timer is
placed onto.</p>

<p>timeformat: A <a href="#class_ba_TimeFormat">ba.TimeFormat</a> value determining how the passed time is
interpreted.</p>

<pre><span><em><small># Example: use a Timer object to print repeatedly for a few seconds:</small></em></span>
def say_it():
    <a href="#function_ba_screenmessage">ba.screenmessage</a>('BADGER!')
def stop_saying_it():
    self.t = None
    <a href="#function_ba_screenmessage">ba.screenmessage</a>('MUSHROOM MUSHROOM!')
<span><em><small># Create our timer; it will run as long as we have the self.t ref.</small></em></span>
self.t = <a href="#class_ba_Timer">ba.Timer</a>(0.3, say_it, repeat=True)
<span><em><small># Now fire off a one-shot timer to kill it.</small></em></span>
<a href="#function_ba_timer">ba.timer</a>(3.89, stop_saying_it)</pre>

<hr>
<h2><strong><a name="class_ba_TimeType">ba.TimeType</a></strong></h3>
<p>Inherits from: <a href="https://docs.python.org/3/library/enum.html#enum.Enum">enum.Enum</a></p>
<p>Specifies the type of time for various operations to target/use.</p>

<p>Category: <a href="#class_category_Enums">Enums</a></p>

<p>    'sim' time is the local simulation time for an activity or session.
       It can proceed at different rates depending on game speed, stops
       for pauses, etc.</p>

<p>    'base' is the baseline time for an activity or session.  It proceeds
       consistently regardless of game speed or pausing, but may stop during
       occurrences such as network outages.</p>

<p>    'real' time is mostly based on clock time, with a few exceptions.  It may
       not advance while the app is backgrounded for instance.  (the engine
       attempts to prevent single large time jumps from occurring)
</p>

<h3>Values:</h3>
<ul>
<li>SIM</li>
<li>BASE</li>
<li>REAL</li>
</ul>
<hr>
<h2><strong><a name="class_ba_UIController">ba.UIController</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Wrangles ba.UILocations.</p>

<p>Category: <a href="#class_category_User_Interface_Classes">User Interface Classes</a>
</p>

<h3>Methods:</h3>
<h5><a href="#method_ba_UIController____init__">&lt;constructor&gt;</a>, <a href="#method_ba_UIController__show_main_menu">show_main_menu()</a></h5>
<dl>
<dt><h4><a name="method_ba_UIController____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.UIController()</span></p>

</dd>
<dt><h4><a name="method_ba_UIController__show_main_menu">show_main_menu()</a></dt></h4><dd>
<p><span>show_main_menu(self, in_game: bool = True) -&gt; None</span></p>

<p>Show the main menu, clearing other UIs from location stacks.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_UIScale">ba.UIScale</a></strong></h3>
<p>Inherits from: <a href="https://docs.python.org/3/library/enum.html#enum.Enum">enum.Enum</a></p>
<p>The overall scale the UI is being rendered for. Note that this is
    independent of pixel resolution. For example, a phone and a desktop PC
    might render the game at similar pixel resolutions but the size they
    display content at will vary significantly.</p>

<p>Category: <a href="#class_category_Enums">Enums</a></p>

<p>    'large' is used for devices such as desktop PCs where fine details can
       be clearly seen. UI elements are generally smaller on the screen
       and more content can be seen at once.</p>

<p>    'medium' is used for devices such as tablets, TVs, or VR headsets.
       This mode strikes a balance between clean readability and amount of
       content visible.</p>

<p>    'small' is used primarily for phones or other small devices where
       content needs to be presented as large and clear in order to remain
       readable from an average distance.
</p>

<h3>Values:</h3>
<ul>
<li>LARGE</li>
<li>MEDIUM</li>
<li>SMALL</li>
</ul>
<hr>
<h2><strong><a name="class_ba_UISubsystem">ba.UISubsystem</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Consolidated UI functionality for the app.</p>

<p>Category: <a href="#class_category_App_Classes">App Classes</a></p>

<p>    To use this class, access the single instance of it at 'ba.app.ui'.
</p>

<h3>Attributes:</h3>
<dl>
<dt><h4><a name="attr_ba_UISubsystem__uiscale">uiscale</a></h4></dt><dd>
<p><span><a href="#class_ba_UIScale">ba.UIScale</a></span></p>
<p>Current ui scale for the app.</p>

</dd>
</dl>
<h3>Methods:</h3>
<h5><a href="#method_ba_UISubsystem____init__">&lt;constructor&gt;</a>, <a href="#method_ba_UISubsystem__clear_main_menu_window">clear_main_menu_window()</a>, <a href="#method_ba_UISubsystem__get_main_menu_location">get_main_menu_location()</a>, <a href="#method_ba_UISubsystem__has_main_menu_window">has_main_menu_window()</a>, <a href="#method_ba_UISubsystem__on_app_launch">on_app_launch()</a>, <a href="#method_ba_UISubsystem__set_main_menu_location">set_main_menu_location()</a>, <a href="#method_ba_UISubsystem__set_main_menu_window">set_main_menu_window()</a></h5>
<dl>
<dt><h4><a name="method_ba_UISubsystem____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.UISubsystem()</span></p>

</dd>
<dt><h4><a name="method_ba_UISubsystem__clear_main_menu_window">clear_main_menu_window()</a></dt></h4><dd>
<p><span>clear_main_menu_window(self, transition: str = None) -&gt; None</span></p>

<p>Clear any existing 'main' window with the provided transition.</p>

</dd>
<dt><h4><a name="method_ba_UISubsystem__get_main_menu_location">get_main_menu_location()</a></dt></h4><dd>
<p><span>get_main_menu_location(self) -&gt; Optional[str]</span></p>

<p>Return the current named main menu location, if any.</p>

</dd>
<dt><h4><a name="method_ba_UISubsystem__has_main_menu_window">has_main_menu_window()</a></dt></h4><dd>
<p><span>has_main_menu_window(self) -&gt; bool</span></p>

<p>Return whether a main menu window is present.</p>

</dd>
<dt><h4><a name="method_ba_UISubsystem__on_app_launch">on_app_launch()</a></dt></h4><dd>
<p><span>on_app_launch(self) -&gt; None</span></p>

<p>Should be run on app launch.</p>

</dd>
<dt><h4><a name="method_ba_UISubsystem__set_main_menu_location">set_main_menu_location()</a></dt></h4><dd>
<p><span>set_main_menu_location(self, location: str) -&gt; None</span></p>

<p>Set the location represented by the current main menu window.</p>

</dd>
<dt><h4><a name="method_ba_UISubsystem__set_main_menu_window">set_main_menu_window()</a></dt></h4><dd>
<p><span>set_main_menu_window(self, window: <a href="#class_ba_Widget">ba.Widget</a>) -&gt; None</span></p>

<p>Set the current 'main' window, replacing any existing.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_Vec3">ba.Vec3</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>A vector of 3 floats.</p>

<p>Category: <a href="#class_category_General_Utility_Classes">General Utility Classes</a></p>

<p>These can be created the following ways (checked in this order):
- with no args, all values are set to 0
- with a single numeric arg, all values are set to that value
- with a single three-member sequence arg, sequence values are copied
- otherwise assumes individual x/y/z args (positional or keywords)</p>

<h3>Attributes:</h3>
<h5><a href="#attr_ba_Vec3__x">x</a>, <a href="#attr_ba_Vec3__y">y</a>, <a href="#attr_ba_Vec3__z">z</a></h5>
<dl>
<dt><h4><a name="attr_ba_Vec3__x">x</a></h4></dt><dd>
<p><span> float</span></p>
<p>The vector's X component.</p>

</dd>
<dt><h4><a name="attr_ba_Vec3__y">y</a></h4></dt><dd>
<p><span> float</span></p>
<p>The vector's Y component.</p>

</dd>
<dt><h4><a name="attr_ba_Vec3__z">z</a></h4></dt><dd>
<p><span> float</span></p>
<p>The vector's Z component.</p>

</dd>
</dl>
<h3>Methods:</h3>
<h5><a href="#method_ba_Vec3__cross">cross()</a>, <a href="#method_ba_Vec3__dot">dot()</a>, <a href="#method_ba_Vec3__length">length()</a>, <a href="#method_ba_Vec3__normalized">normalized()</a></h5>
<dl>
<dt><h4><a name="method_ba_Vec3__cross">cross()</a></dt></h4><dd>
<p><span>cross(other: Vec3) -&gt; Vec3</span></p>

<p>Returns the cross product of this vector and another.</p>

</dd>
<dt><h4><a name="method_ba_Vec3__dot">dot()</a></dt></h4><dd>
<p><span>dot(other: Vec3) -&gt; float</span></p>

<p>Returns the dot product of this vector and another.</p>

</dd>
<dt><h4><a name="method_ba_Vec3__length">length()</a></dt></h4><dd>
<p><span>length() -&gt; float</span></p>

<p>Returns the length of the vector.</p>

</dd>
<dt><h4><a name="method_ba_Vec3__normalized">normalized()</a></dt></h4><dd>
<p><span>normalized() -&gt; Vec3</span></p>

<p>Returns a normalized version of the vector.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_WeakCall">ba.WeakCall</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Wrap a callable and arguments into a single callable object.</p>

<p>Category: <a href="#class_category_General_Utility_Classes">General Utility Classes</a></p>

<p>    When passed a bound method as the callable, the instance portion
    of it is weak-referenced, meaning the underlying instance is
    free to die if all other references to it go away. Should this
    occur, calling the WeakCall is simply a no-op.</p>

<p>    Think of this as a handy way to tell an object to do something
    at some point in the future if it happens to still exist.</p>

<pre><span><em><small>    # EXAMPLE A: this code will create a FooClass instance and call its</small></em></span>
<span><em><small>    # bar() method 5 seconds later; it will be kept alive even though</small></em></span>
<span><em><small>    # we overwrite its variable with None because the bound method</small></em></span>
<span><em><small>    # we pass as a timer callback (foo.bar) strong-references it</small></em></span>
    foo = FooClass()
    <a href="#function_ba_timer">ba.timer</a>(5.0, foo.bar)
    foo = None</pre>

<pre><span><em><small>    # EXAMPLE B: this code will *not* keep our object alive; it will die</small></em></span>
<span><em><small>    # when we overwrite it with None and the timer will be a no-op when it</small></em></span>
<span><em><small>    # fires</small></em></span>
    foo = FooClass()
    <a href="#function_ba_timer">ba.timer</a>(5.0, <a href="#class_ba_WeakCall">ba.WeakCall</a>(foo.bar))
    foo = None</pre>

<p>    Note: additional args and keywords you provide to the WeakCall()
    constructor are stored as regular strong-references; you'll need
    to wrap them in weakrefs manually if desired.
</p>

<h3>Methods:</h3>
<dl>
<dt><h4><a name="method_ba_WeakCall____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.WeakCall(*args: Any, **keywds: Any)</span></p>

<p>Instantiate a WeakCall.</p>

<p>Pass a callable as the first arg, followed by any number of
arguments or keywords.</p>

<pre><span><em><small># Example: wrap a method call with some positional and</small></em></span>
<span><em><small># keyword args:</small></em></span>
myweakcall = ba.WeakCall(myobj.dostuff, argval1, namedarg=argval2)</pre>

<pre><span><em><small># Now we have a single callable to run that whole mess.</small></em></span>
<span><em><small># The same as calling myobj.dostuff(argval1, namedarg=argval2)</small></em></span>
<span><em><small># (provided my_obj still exists; this will do nothing otherwise)</small></em></span>
myweakcall()</pre>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_Widget">ba.Widget</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>Internal type for low level UI elements; buttons, windows, etc.</p>

<p>Category: <a href="#class_category_User_Interface_Classes">User Interface Classes</a></p>

<p>This class represents a weak reference to a widget object
in the internal c++ layer. Currently, functions such as
<a href="#function_ba_buttonwidget">ba.buttonwidget</a>() must be used to instantiate or edit these.</p>

<h3>Methods:</h3>
<h5><a href="#method_ba_Widget__activate">activate()</a>, <a href="#method_ba_Widget__add_delete_callback">add_delete_callback()</a>, <a href="#method_ba_Widget__delete">delete()</a>, <a href="#method_ba_Widget__exists">exists()</a>, <a href="#method_ba_Widget__get_children">get_children()</a>, <a href="#method_ba_Widget__get_screen_space_center">get_screen_space_center()</a>, <a href="#method_ba_Widget__get_selected_child">get_selected_child()</a>, <a href="#method_ba_Widget__get_widget_type">get_widget_type()</a></h5>
<dl>
<dt><h4><a name="method_ba_Widget__activate">activate()</a></dt></h4><dd>
<p><span>activate() -&gt; None</span></p>

<p>Activates a widget; the same as if it had been clicked.</p>

</dd>
<dt><h4><a name="method_ba_Widget__add_delete_callback">add_delete_callback()</a></dt></h4><dd>
<p><span>add_delete_callback(call: Callable) -&gt; None</span></p>

<p>Add a call to be run immediately after this widget is destroyed.</p>

</dd>
<dt><h4><a name="method_ba_Widget__delete">delete()</a></dt></h4><dd>
<p><span>delete(ignore_missing: bool = True) -&gt; None</span></p>

<p>Delete the Widget.  Ignores already-deleted Widgets if ignore_missing
  is True; otherwise an Exception is thrown.</p>

</dd>
<dt><h4><a name="method_ba_Widget__exists">exists()</a></dt></h4><dd>
<p><span>exists() -&gt; bool</span></p>

<p>Returns whether the Widget still exists.
Most functionality will fail on a nonexistent widget.</p>

<p>Note that you can also use the boolean operator for this same
functionality, so a statement such as "if mywidget" will do
the right thing both for Widget objects and values of None.</p>

</dd>
<dt><h4><a name="method_ba_Widget__get_children">get_children()</a></dt></h4><dd>
<p><span>get_children() -&gt; List[<a href="#class_ba_Widget">ba.Widget</a>]</span></p>

<p>Returns any child Widgets of this Widget.</p>

</dd>
<dt><h4><a name="method_ba_Widget__get_screen_space_center">get_screen_space_center()</a></dt></h4><dd>
<p><span>get_screen_space_center() -&gt; Tuple[float, float]</span></p>

<p>Returns the coords of the Widget center relative to the center of the
screen. This can be useful for placing pop-up windows and other special
cases.</p>

</dd>
<dt><h4><a name="method_ba_Widget__get_selected_child">get_selected_child()</a></dt></h4><dd>
<p><span>get_selected_child() -&gt; Optional[<a href="#class_ba_Widget">ba.Widget</a>]</span></p>

<p>Returns the selected child Widget or None if nothing is selected.</p>

</dd>
<dt><h4><a name="method_ba_Widget__get_widget_type">get_widget_type()</a></dt></h4><dd>
<p><span>get_widget_type() -&gt; str</span></p>

<p>Return the internal type of the Widget as a string.  Note that this is
different from the Python <a href="#class_ba_Widget">ba.Widget</a> type, which is the same for all
widgets.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="class_ba_WidgetNotFoundError">ba.WidgetNotFoundError</a></strong></h3>
<p>Inherits from: <a href="#class_ba_NotFoundError">ba.NotFoundError</a>, <a href="https://docs.python.org/3/library/exceptions.html#Exception">Exception</a>, <a href="https://docs.python.org/3/library/exceptions.html#BaseException">BaseException</a></p>
<p>Exception raised when an expected <a href="#class_ba_Widget">ba.Widget</a> does not exist.</p>

<p>Category: <a href="#class_category_Exception_Classes">Exception Classes</a>
</p>

<h3>Methods:</h3>
<p>&lt;all methods inherited from <a href="#class_ba_NotFoundError">ba.NotFoundError</a>&gt;</p>
<hr>
<h2><strong><a name="class_ba_Window">ba.Window</a></strong></h3>
<p><em>&lt;top level class&gt;</em>
</p>
<p>A basic window.</p>

<p>Category: <a href="#class_category_User_Interface_Classes">User Interface Classes</a>
</p>

<h3>Methods:</h3>
<h5><a href="#method_ba_Window____init__">&lt;constructor&gt;</a>, <a href="#method_ba_Window__get_root_widget">get_root_widget()</a></h5>
<dl>
<dt><h4><a name="method_ba_Window____init__">&lt;constructor&gt;</a></dt></h4><dd>
<p><span>ba.Window(root_widget: <a href="#class_ba_Widget">ba.Widget</a>, cleanupcheck: bool = True)</span></p>

</dd>
<dt><h4><a name="method_ba_Window__get_root_widget">get_root_widget()</a></dt></h4><dd>
<p><span>get_root_widget(self) -&gt; <a href="#class_ba_Widget">ba.Widget</a></span></p>

<p>Return the root widget.</p>

</dd>
</dl>
<hr>
<h2><strong><a name="function_ba_animate">ba.animate()</a></strong></h3>
<p><span>animate(node: <a href="#class_ba_Node">ba.Node</a>, attr: str, keys: Dict[float, float], loop: bool = False, offset: float = 0, timetype: <a href="#class_ba_TimeType">ba.TimeType</a> = &lt;TimeType.SIM: 0&gt;, timeformat: <a href="#class_ba_TimeFormat">ba.TimeFormat</a> = &lt;TimeFormat.SECONDS: 0&gt;, suppress_format_warning: bool = False) -&gt; <a href="#class_ba_Node">ba.Node</a></span></p>

<p>Animate values on a target <a href="#class_ba_Node">ba.Node</a>.</p>

<p>Category: <a href="#function_category_Gameplay_Functions">Gameplay Functions</a></p>

<p>Creates an 'animcurve' node with the provided values and time as an input,
connect it to the provided attribute, and set it to die with the target.
Key values are provided as time:value dictionary pairs.  Time values are
relative to the current time. By default, times are specified in seconds,
but timeformat can also be set to MILLISECONDS to recreate the old behavior
(prior to ba 1.5) of taking milliseconds. Returns the animcurve node.</p>

<hr>
<h2><strong><a name="function_ba_animate_array">ba.animate_array()</a></strong></h3>
<p><span>animate_array(node: <a href="#class_ba_Node">ba.Node</a>, attr: str, size: int, keys: Dict[float, Sequence[float]], loop: bool = False, offset: float = 0, timetype: <a href="#class_ba_TimeType">ba.TimeType</a> = &lt;TimeType.SIM: 0&gt;, timeformat: <a href="#class_ba_TimeFormat">ba.TimeFormat</a> = &lt;TimeFormat.SECONDS: 0&gt;, suppress_format_warning: bool = False) -&gt; None</span></p>

<p>Animate an array of values on a target <a href="#class_ba_Node">ba.Node</a>.</p>

<p>Category: <a href="#function_category_Gameplay_Functions">Gameplay Functions</a></p>

<p>Like <a href="#function_ba_animate">ba.animate</a>(), but operates on array attributes.</p>

<hr>
<h2><strong><a name="function_ba_buttonwidget">ba.buttonwidget()</a></strong></h3>
<p><span>buttonwidget(edit: <a href="#class_ba_Widget">ba.Widget</a> = None,
  parent: <a href="#class_ba_Widget">ba.Widget</a> = None,
  size: Sequence[float] = None,
  position: Sequence[float] = None,
  on_activate_call: Callable = None,
  label: Union[str, <a href="#class_ba_Lstr">ba.Lstr</a>] = None,
  color: Sequence[float] = None,
  down_widget: <a href="#class_ba_Widget">ba.Widget</a> = None,
  up_widget: <a href="#class_ba_Widget">ba.Widget</a> = None,
  left_widget: <a href="#class_ba_Widget">ba.Widget</a> = None,
  right_widget: <a href="#class_ba_Widget">ba.Widget</a> = None,
  texture: <a href="#class_ba_Texture">ba.Texture</a> = None,
  text_scale: float = None,
  textcolor: Sequence[float] = None,
  enable_sound: bool = None,
  model_transparent: <a href="#class_ba_Model">ba.Model</a> = None,
  model_opaque: <a href="#class_ba_Model">ba.Model</a> = None,
  repeat: bool = None,
  scale: float = None,
  transition_delay: float = None,
  on_select_call: Callable = None,
  button_type: str = None,
  extra_touch_border_scale: float = None,
  selectable: bool = None,
  show_buffer_top: float = None,
  icon: <a href="#class_ba_Texture">ba.Texture</a> = None,
  iconscale: float = None,
  icon_tint: float = None,
  icon_color: Sequence[float] = None,
  autoselect: bool = None,
  mask_texture: <a href="#class_ba_Texture">ba.Texture</a> = None,
  tint_texture: <a href="#class_ba_Texture">ba.Texture</a> = None,
  tint_color: Sequence[float] = None,
  tint2_color: Sequence[float] = None,
  text_flatness: float = None,
  text_res_scale: float = None,
  enabled: bool = None) -&gt; <a href="#class_ba_Widget">ba.Widget</a></span></p>

<p>Create or edit a button widget.</p>

<p>Category: <a href="#function_category_User_Interface_Functions">User Interface Functions</a></p>

<p>Pass a valid existing <a href="#class_ba_Widget">ba.Widget</a> as 'edit' to modify it; otherwise
a new one is created and returned. Arguments that are not set to None
are applied to the Widget.</p>

<hr>
<h2><strong><a name="function_ba_cameraflash">ba.cameraflash()</a></strong></h3>
<p><span>cameraflash(duration: float = 999.0) -&gt; None</span></p>

<p>Create a strobing camera flash effect.</p>

<p>Category: <a href="#function_category_Gameplay_Functions">Gameplay Functions</a></p>

<p>(as seen when a team wins a game)
Duration is in seconds.</p>

<hr>
<h2><strong><a name="function_ba_camerashake">ba.camerashake()</a></strong></h3>
<p><span>camerashake(intensity: float = 1.0) -&gt; None</span></p>

<p>Shake the camera.</p>

<p>Category: <a href="#function_category_Gameplay_Functions">Gameplay Functions</a></p>

<p>Note that some cameras and/or platforms (such as VR) may not display
camera-shake, so do not rely on this always being visible to the
player as a gameplay cue.</p>

<hr>
<h2><strong><a name="function_ba_charstr">ba.charstr()</a></strong></h3>
<p><span>charstr(char_id: <a href="#class_ba_SpecialChar">ba.SpecialChar</a>) -&gt; str</span></p>

<p>Get a unicode string representing a special character.</p>

<p>Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p>Note that these utilize the private-use block of unicode characters
(U+E000-U+F8FF) and are specific to the game; exporting or rendering
them elsewhere will be meaningless.</p>

<p>see <a href="#class_ba_SpecialChar">ba.SpecialChar</a> for the list of available characters.</p>

<hr>
<h2><strong><a name="function_ba_checkboxwidget">ba.checkboxwidget()</a></strong></h3>
<p><span>checkboxwidget(edit: <a href="#class_ba_Widget">ba.Widget</a> = None,
  parent: <a href="#class_ba_Widget">ba.Widget</a> = None,
  size: Sequence[float] = None,
  position: Sequence[float] = None,
  text: Union[<a href="#class_ba_Lstr">ba.Lstr</a>, str] = None,
  value: bool = None,
  on_value_change_call: Callable[[bool], None] = None,
  on_select_call: Callable[[], None] = None,
  text_scale: float = None,
  textcolor: Sequence[float] = None,
  scale: float = None,
  is_radio_button: bool = None,
  maxwidth: float = None,
  autoselect: bool = None,
  color: Sequence[float] = None) -&gt; <a href="#class_ba_Widget">ba.Widget</a></span></p>

<p>Create or edit a check-box widget.</p>

<p>Category: <a href="#function_category_User_Interface_Functions">User Interface Functions</a></p>

<p>Pass a valid existing <a href="#class_ba_Widget">ba.Widget</a> as 'edit' to modify it; otherwise
a new one is created and returned. Arguments that are not set to None
are applied to the Widget.</p>

<hr>
<h2><strong><a name="function_ba_clipboard_get_text">ba.clipboard_get_text()</a></strong></h3>
<p><span>clipboard_get_text() -&gt; str</span></p>

<p>Return text currently on the system clipboard.</p>

<p>Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p>Ensure that <a href="#function_ba_clipboard_has_text">ba.clipboard_has_text</a>() returns True before calling
 this function.</p>

<hr>
<h2><strong><a name="function_ba_clipboard_has_text">ba.clipboard_has_text()</a></strong></h3>
<p><span>clipboard_has_text() -&gt; bool</span></p>

<p>Return whether there is currently text on the clipboard.</p>

<p>Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p>This will return False if no system clipboard is available; no need
 to call ba.clipboard_available() separately.</p>

<hr>
<h2><strong><a name="function_ba_clipboard_is_supported">ba.clipboard_is_supported()</a></strong></h3>
<p><span>clipboard_is_supported() -&gt; bool</span></p>

<p>Return whether this platform supports clipboard operations at all.</p>

<p>Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p>If this returns False, UIs should not show 'copy to clipboard'
buttons, etc.</p>

<hr>
<h2><strong><a name="function_ba_clipboard_set_text">ba.clipboard_set_text()</a></strong></h3>
<p><span>clipboard_set_text(value: str) -&gt; None</span></p>

<p>Copy a string to the system clipboard.</p>

<p>Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p>Ensure that ba.clipboard_available() returns True before adding
 buttons/etc. that make use of this functionality.</p>

<hr>
<h2><strong><a name="function_ba_columnwidget">ba.columnwidget()</a></strong></h3>
<p><span>columnwidget(edit: <a href="#class_ba_Widget">ba.Widget</a> = None,
  parent: <a href="#class_ba_Widget">ba.Widget</a> = None,
  size: Sequence[float] = None,
  position: Sequence[float] = None,
  background: bool = None,
  selected_child: <a href="#class_ba_Widget">ba.Widget</a> = None,
  visible_child: <a href="#class_ba_Widget">ba.Widget</a> = None,
  single_depth: bool = None,
  print_list_exit_instructions: bool = None,
  left_border: float = None,
  top_border: float = None,
  bottom_border: float = None,
  selection_loops_to_parent: bool = None,
  border: float = None,
  margin: float = None,
  claims_left_right: bool = None,
  claims_tab: bool = None) -&gt; <a href="#class_ba_Widget">ba.Widget</a></span></p>

<p>Create or edit a column widget.</p>

<p>Category: <a href="#function_category_User_Interface_Functions">User Interface Functions</a></p>

<p>Pass a valid existing <a href="#class_ba_Widget">ba.Widget</a> as 'edit' to modify it; otherwise
a new one is created and returned. Arguments that are not set to None
are applied to the Widget.</p>

<hr>
<h2><strong><a name="function_ba_containerwidget">ba.containerwidget()</a></strong></h3>
<p><span>containerwidget(edit: <a href="#class_ba_Widget">ba.Widget</a> = None,
  parent: <a href="#class_ba_Widget">ba.Widget</a> = None,
  size: Sequence[float] = None,
  position: Sequence[float] = None,
  background: bool = None,
  selected_child: <a href="#class_ba_Widget">ba.Widget</a> = None,
  transition: str = None,
  cancel_button: <a href="#class_ba_Widget">ba.Widget</a> = None,
  start_button: <a href="#class_ba_Widget">ba.Widget</a> = None,
  root_selectable: bool = None,
  on_activate_call: Callable[[], None] = None,
  claims_left_right: bool = None,
  claims_tab: bool = None,
  selection_loops: bool = None,
  selection_loops_to_parent: bool = None,
  scale: float = None,
  on_outside_click_call: Callable[[], None] = None,
  single_depth: bool = None,
  visible_child: <a href="#class_ba_Widget">ba.Widget</a> = None,
  stack_offset: Sequence[float] = None,
  color: Sequence[float] = None,
  on_cancel_call: Callable[[], None] = None,
  print_list_exit_instructions: bool = None,
  click_activate: bool = None,
  always_highlight: bool = None,
  selectable: bool = None,
  scale_origin_stack_offset: Sequence[float] = None,
  toolbar_visibility: str = None,
  on_select_call: Callable[[], None] = None,
  claim_outside_clicks: bool = None,
  claims_up_down: bool = None) -&gt; <a href="#class_ba_Widget">ba.Widget</a></span></p>

<p>Create or edit a container widget.</p>

<p>Category: <a href="#function_category_User_Interface_Functions">User Interface Functions</a></p>

<p>Pass a valid existing <a href="#class_ba_Widget">ba.Widget</a> as 'edit' to modify it; otherwise
a new one is created and returned. Arguments that are not set to None
are applied to the Widget.</p>

<hr>
<h2><strong><a name="function_ba_do_once">ba.do_once()</a></strong></h3>
<p><span>do_once() -&gt; bool</span></p>

<p>Return whether this is the first time running a line of code.</p>

<p>Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p>This is used by 'print_once()' type calls to keep from overflowing
logs. The call functions by registering the filename and line where
The call is made from.  Returns True if this location has not been
registered already, and False if it has.</p>

<pre><span><em><small># Example: this print will only fire for the first loop iteration:</small></em></span>
for i in range(10):
    if <a href="#function_ba_do_once">ba.do_once</a>():
        print('Hello once from loop!')</pre>

<hr>
<h2><strong><a name="function_ba_emitfx">ba.emitfx()</a></strong></h3>
<p><span>emitfx(position: Sequence[float],
  velocity: Optional[Sequence[float]] = None,
  count: int = 10, scale: float = 1.0, spread: float = 1.0,
  chunk_type: str = 'rock', emit_type: str ='chunks',
  tendril_type: str = 'smoke') -&gt; None</span></p>

<p>Emit particles, smoke, etc. into the fx sim layer.</p>

<p>Category: <a href="#function_category_Gameplay_Functions">Gameplay Functions</a></p>

<p>The fx sim layer is a secondary dynamics simulation that runs in
the background and just looks pretty; it does not affect gameplay.
Note that the actual amount emitted may vary depending on graphics
settings, exiting element counts, or other factors.</p>

<hr>
<h2><strong><a name="function_ba_existing">ba.existing()</a></strong></h3>
<p><span>existing(obj: Optional[ExistableType]) -&gt; Optional[ExistableType]</span></p>

<p>Convert invalid references to None for any <a href="#class_ba_Existable">ba.Existable</a> object.</p>

<p>Category: <a href="#function_category_Gameplay_Functions">Gameplay Functions</a></p>

<p>To best support type checking, it is important that invalid references
not be passed around and instead get converted to values of None.
That way the type checker can properly flag attempts to pass dead
objects (Optional[FooType]) into functions expecting only live ones
(FooType), etc. This call can be used on any 'existable' object
(one with an exists() method) and will convert it to a None value
if it does not exist.</p>

<p>For more info, see notes on 'existables' here:
https://ballistica.net/wiki/Coding-Style-Guide</p>

<hr>
<h2><strong><a name="function_ba_garbage_collect">ba.garbage_collect()</a></strong></h3>
<p><span>garbage_collect() -&gt; None</span></p>

<p>Run an explicit pass of garbage collection.</p>

<p>Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p>May also print warnings/etc. if collection takes too long or if
uncollectible objects are found (so use this instead of simply
gc.collect().</p>

<hr>
<h2><strong><a name="function_ba_getactivity">ba.getactivity()</a></strong></h3>
<p><span>getactivity(doraise: bool = True) -&gt; &lt;varies&gt;</span></p>

<p>Return the current <a href="#class_ba_Activity">ba.Activity</a> instance.</p>

<p>Category: <a href="#function_category_Gameplay_Functions">Gameplay Functions</a></p>

<p>Note that this is based on context; thus code run in a timer generated
in Activity 'foo' will properly return 'foo' here, even if another
Activity has since been created or is transitioning in.
If there is no current Activity, raises a <a href="#class_ba_ActivityNotFoundError">ba.ActivityNotFoundError</a>.
If doraise is False, None will be returned instead in that case.</p>

<hr>
<h2><strong><a name="function_ba_getclass">ba.getclass()</a></strong></h3>
<p><span>getclass(name: str, subclassof: Type[T]) -&gt; Type[T]</span></p>

<p>Given a full class name such as foo.bar.MyClass, return the class.</p>

<p>Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p>The class will be checked to make sure it is a subclass of the provided
'subclassof' class, and a TypeError will be raised if not.</p>

<hr>
<h2><strong><a name="function_ba_getcollidemodel">ba.getcollidemodel()</a></strong></h3>
<p><span>getcollidemodel(name: str) -&gt; <a href="#class_ba_CollideModel">ba.CollideModel</a></span></p>

<p>Return a collide-model, loading it if necessary.</p>

<p>Category: <a href="#function_category_Asset_Functions">Asset Functions</a></p>

<p>Collide-models are used in physics calculations for such things as
terrain.</p>

<p>Note that this function returns immediately even if the media has yet
to be loaded. To avoid hitches, instantiate your media objects in
advance of when you will be using them, allowing time for them to load
in the background if necessary.</p>

<hr>
<h2><strong><a name="function_ba_getcollision">ba.getcollision()</a></strong></h3>
<p><span>getcollision() -&gt; Collision</span></p>

<p>Return the in-progress collision.</p>

<p>Category: <a href="#function_category_Gameplay_Functions">Gameplay Functions</a></p>

<hr>
<h2><strong><a name="function_ba_getmaps">ba.getmaps()</a></strong></h3>
<p><span>getmaps(playtype: str) -&gt; List[str]</span></p>

<p>Return a list of <a href="#class_ba_Map">ba.Map</a> types supporting a playtype str.</p>

<p>Category: <a href="#function_category_Asset_Functions">Asset Functions</a></p>

<p>Maps supporting a given playtype must provide a particular set of
features and lend themselves to a certain style of play.</p>

<p><strong>Play Types:</strong></p>

<p>'melee'
  General fighting map.
  Has one or more 'spawn' locations.</p>

<p>'team_flag'
  For games such as Capture The Flag where each team spawns by a flag.
  Has two or more 'spawn' locations, each with a corresponding 'flag'
  location (based on index).</p>

<p>'single_flag'
  For games such as King of the Hill or Keep Away where multiple teams
  are fighting over a single flag.
  Has two or more 'spawn' locations and 1 'flag_default' location.</p>

<p>'conquest'
  For games such as Conquest where flags are spread throughout the map
  - has 2+ 'flag' locations, 2+ 'spawn_by_flag' locations.</p>

<p>'king_of_the_hill' - has 2+ 'spawn' locations, 1+ 'flag_default' locations,
                     and 1+ 'powerup_spawn' locations</p>

<p>'hockey'
  For hockey games.
  Has two 'goal' locations, corresponding 'spawn' locations, and one
  'flag_default' location (for where puck spawns)</p>

<p>'football'
  For football games.
  Has two 'goal' locations, corresponding 'spawn' locations, and one
  'flag_default' location (for where flag/ball/etc. spawns)</p>

<p>'race'
  For racing games where players much touch each region in order.
  Has two or more 'race_point' locations.</p>

<hr>
<h2><strong><a name="function_ba_getmodel">ba.getmodel()</a></strong></h3>
<p><span>getmodel(name: str) -&gt; <a href="#class_ba_Model">ba.Model</a></span></p>

<p>Return a model, loading it if necessary.</p>

<p>Category: <a href="#function_category_Asset_Functions">Asset Functions</a></p>

<p>Note that this function returns immediately even if the media has yet
to be loaded. To avoid hitches, instantiate your media objects in
advance of when you will be using them, allowing time for them to load
in the background if necessary.</p>

<hr>
<h2><strong><a name="function_ba_getnodes">ba.getnodes()</a></strong></h3>
<p><span>getnodes() -&gt; list</span></p>

<p>Return all nodes in the current <a href="#class_ba_Context">ba.Context</a>.
Category: <a href="#function_category_Gameplay_Functions">Gameplay Functions</a></p>

<hr>
<h2><strong><a name="function_ba_getsession">ba.getsession()</a></strong></h3>
<p><span>getsession(doraise: bool = True) -&gt; &lt;varies&gt;</span></p>

<p>Category: <a href="#function_category_Gameplay_Functions">Gameplay Functions</a></p>

<p>Returns the current <a href="#class_ba_Session">ba.Session</a> instance.
Note that this is based on context; thus code being run in the UI
context will return the UI context here even if a game Session also
exists, etc. If there is no current Session, an Exception is raised, or
if doraise is False then None is returned instead.</p>

<hr>
<h2><strong><a name="function_ba_getsound">ba.getsound()</a></strong></h3>
<p><span>getsound(name: str) -&gt; <a href="#class_ba_Sound">ba.Sound</a></span></p>

<p>Return a sound, loading it if necessary.</p>

<p>Category: <a href="#function_category_Asset_Functions">Asset Functions</a></p>

<p>Note that this function returns immediately even if the media has yet
to be loaded. To avoid hitches, instantiate your media objects in
advance of when you will be using them, allowing time for them to load
in the background if necessary.</p>

<hr>
<h2><strong><a name="function_ba_gettexture">ba.gettexture()</a></strong></h3>
<p><span>gettexture(name: str) -&gt; <a href="#class_ba_Texture">ba.Texture</a></span></p>

<p>Return a texture, loading it if necessary.</p>

<p>Category: <a href="#function_category_Asset_Functions">Asset Functions</a></p>

<p>Note that this function returns immediately even if the media has yet
to be loaded. To avoid hitches, instantiate your media objects in
advance of when you will be using them, allowing time for them to load
in the background if necessary.</p>

<hr>
<h2><strong><a name="function_ba_hscrollwidget">ba.hscrollwidget()</a></strong></h3>
<p><span>hscrollwidget(edit: <a href="#class_ba_Widget">ba.Widget</a> = None, parent: <a href="#class_ba_Widget">ba.Widget</a> = None,
  size: Sequence[float] = None, position: Sequence[float] = None,
  background: bool = None, selected_child: <a href="#class_ba_Widget">ba.Widget</a> = None,
  capture_arrows: bool = None,
  on_select_call: Callable[[], None] = None,
  center_small_content: bool = None, color: Sequence[float] = None,
  highlight: bool = None, border_opacity: float = None,
  simple_culling_h: float = None,
  claims_left_right: bool = None,
  claims_up_down: bool = None,
  claims_tab: bool = None)  -&gt; <a href="#class_ba_Widget">ba.Widget</a></span></p>

<p>Create or edit a horizontal scroll widget.</p>

<p>Category: <a href="#function_category_User_Interface_Functions">User Interface Functions</a></p>

<p>Pass a valid existing <a href="#class_ba_Widget">ba.Widget</a> as 'edit' to modify it; otherwise
a new one is created and returned. Arguments that are not set to None
are applied to the Widget.</p>

<hr>
<h2><strong><a name="function_ba_imagewidget">ba.imagewidget()</a></strong></h3>
<p><span>imagewidget(edit: <a href="#class_ba_Widget">ba.Widget</a> = None, parent: <a href="#class_ba_Widget">ba.Widget</a> = None,
  size: Sequence[float] = None, position: Sequence[float] = None,
  color: Sequence[float] = None, texture: <a href="#class_ba_Texture">ba.Texture</a> = None,
  opacity: float = None, model_transparent: <a href="#class_ba_Model">ba.Model</a> = None,
  model_opaque: <a href="#class_ba_Model">ba.Model</a> = None, has_alpha_channel: bool = True,
  tint_texture: <a href="#class_ba_Texture">ba.Texture</a> = None, tint_color: Sequence[float] = None,
  transition_delay: float = None, draw_controller: <a href="#class_ba_Widget">ba.Widget</a> = None,
  tint2_color: Sequence[float] = None, tilt_scale: float = None,
  mask_texture: <a href="#class_ba_Texture">ba.Texture</a> = None, radial_amount: float = None)
  -&gt; <a href="#class_ba_Widget">ba.Widget</a></span></p>

<p>Create or edit an image widget.</p>

<p>Category: <a href="#function_category_User_Interface_Functions">User Interface Functions</a></p>

<p>Pass a valid existing <a href="#class_ba_Widget">ba.Widget</a> as 'edit' to modify it; otherwise
a new one is created and returned. Arguments that are not set to None
are applied to the Widget.</p>

<hr>
<h2><strong><a name="function_ba_is_browser_likely_available">ba.is_browser_likely_available()</a></strong></h3>
<p><span>is_browser_likely_available() -&gt; bool</span></p>

<p>Return whether a browser likely exists on the current device.</p>

<p>Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p>If this returns False you may want to avoid calling ba.show_url()
with any lengthy addresses. (ba.show_url() will display an address
as a string in a window if unable to bring up a browser, but that
is only useful for simple URLs.)</p>

<hr>
<h2><strong><a name="function_ba_is_point_in_box">ba.is_point_in_box()</a></strong></h3>
<p><span>is_point_in_box(pnt: Sequence[float], box: Sequence[float]) -&gt; bool</span></p>

<p>Return whether a given point is within a given box.</p>

<p>Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p>For use with standard def boxes (position|rotate|scale).</p>

<hr>
<h2><strong><a name="function_ba_log">ba.log()</a></strong></h3>
<p><span>log(message: str, to_stdout: bool = True,
    to_server: bool = True) -&gt; None</span></p>

<p>Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p>Log a message. This goes to the default logging mechanism depending
on the platform (stdout on mac, android log on android, etc).</p>

<p>Log messages also go to the in-game console unless 'to_console'
is False. They are also sent to the master-server for use in analyzing
issues unless to_server is False.</p>

<p>Python's standard print() is wired to call this (with default values)
so in most cases you can just use that.</p>

<hr>
<h2><strong><a name="function_ba_newactivity">ba.newactivity()</a></strong></h3>
<p><span>newactivity(activity_type: Type[<a href="#class_ba_Activity">ba.Activity</a>],
  settings: dict = None) -&gt; <a href="#class_ba_Activity">ba.Activity</a></span></p>

<p>Instantiates a <a href="#class_ba_Activity">ba.Activity</a> given a type object.</p>

<p>Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p>Activities require special setup and thus cannot be directly
instantiated; you must go through this function.</p>

<hr>
<h2><strong><a name="function_ba_newnode">ba.newnode()</a></strong></h3>
<p><span>newnode(type: str, owner: <a href="#class_ba_Node">ba.Node</a> = None,
attrs: dict = None, name: str = None, delegate: Any = None)
 -&gt; Node</span></p>

<p>Add a node of the given type to the game.</p>

<p>Category: <a href="#function_category_Gameplay_Functions">Gameplay Functions</a></p>

<p>If a dict is provided for 'attributes', the node's initial attributes
will be set based on them.</p>

<p>'name', if provided, will be stored with the node purely for debugging
purposes. If no name is provided, an automatic one will be generated
such as 'terrain@foo.py:30'.</p>

<p>If 'delegate' is provided, Python messages sent to the node will go to
that object's handlemessage() method. Note that the delegate is stored
as a weak-ref, so the node itself will not keep the object alive.</p>

<p>if 'owner' is provided, the node will be automatically killed when that
object dies. 'owner' can be another node or a <a href="#class_ba_Actor">ba.Actor</a></p>

<hr>
<h2><strong><a name="function_ba_normalized_color">ba.normalized_color()</a></strong></h3>
<p><span>normalized_color(color: Sequence[float]) -&gt; Tuple[float, ...]</span></p>

<p>Scale a color so its largest value is 1; useful for coloring lights.</p>

<p>Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<hr>
<h2><strong><a name="function_ba_open_url">ba.open_url()</a></strong></h3>
<p><span>open_url(address: str) -&gt; None</span></p>

<p>Open a provided URL.</p>

<p>Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p>Open the provided url in a web-browser, or display the URL
string in a window if that isn't possible.</p>

<hr>
<h2><strong><a name="function_ba_playsound">ba.playsound()</a></strong></h3>
<p><span>playsound(sound: Sound, volume: float = 1.0,
  position: Sequence[float] = None, host_only: bool = False) -&gt; None</span></p>

<p>Play a <a href="#class_ba_Sound">ba.Sound</a> a single time.</p>

<p>Category: <a href="#function_category_Gameplay_Functions">Gameplay Functions</a></p>

<p>If position is not provided, the sound will be at a constant volume
everywhere.  Position should be a float tuple of size 3.</p>

<hr>
<h2><strong><a name="function_ba_print_error">ba.print_error()</a></strong></h3>
<p><span>print_error(err_str: str, once: bool = False) -&gt; None</span></p>

<p>Print info about an error along with pertinent context state.</p>

<p>Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p>Prints all positional arguments provided along with various info about the
current context.
Pass the keyword 'once' as True if you want the call to only happen
one time from an exact calling location.</p>

<hr>
<h2><strong><a name="function_ba_print_exception">ba.print_exception()</a></strong></h3>
<p><span>print_exception(*args: Any, **keywds: Any) -&gt; None</span></p>

<p>Print info about an exception along with pertinent context state.</p>

<p>Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p>Prints all arguments provided along with various info about the
current context and the outstanding exception.
Pass the keyword 'once' as True if you want the call to only happen
one time from an exact calling location.</p>

<hr>
<h2><strong><a name="function_ba_printnodes">ba.printnodes()</a></strong></h3>
<p><span>printnodes() -&gt; None</span></p>

<p>Print various info about existing nodes; useful for debugging.</p>

<p>Category: <a href="#function_category_Gameplay_Functions">Gameplay Functions</a></p>

<hr>
<h2><strong><a name="function_ba_printobjects">ba.printobjects()</a></strong></h3>
<p><span>printobjects() -&gt; None</span></p>

<p>Print debugging info about game objects.</p>

<p>Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p>This call only functions in debug builds of the game.
It prints various info about the current object count, etc.</p>

<hr>
<h2><strong><a name="function_ba_pushcall">ba.pushcall()</a></strong></h3>
<p><span>pushcall(call: Callable, from_other_thread: bool = False,
     suppress_other_thread_warning: bool = False ) -&gt; None</span></p>

<p>Pushes a call onto the event loop to be run during the next cycle.</p>

<p>Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p>This can be handy for calls that are disallowed from within other
callbacks, etc.</p>

<p>This call expects to be used in the game thread, and will automatically
save and restore the <a href="#class_ba_Context">ba.Context</a> to behave seamlessly.</p>

<p>If you want to push a call from outside of the game thread,
however, you can pass 'from_other_thread' as True. In this case
the call will always run in the UI context on the game thread.</p>

<hr>
<h2><strong><a name="function_ba_quit">ba.quit()</a></strong></h3>
<p><span>quit(soft: bool = False, back: bool = False) -&gt; None</span></p>

<p>Quit the game.</p>

<p>Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p>On systems like android, 'soft' will end the activity but keep the
app running.</p>

<hr>
<h2><strong><a name="function_ba_rowwidget">ba.rowwidget()</a></strong></h3>
<p><span>rowwidget(edit: <a href="#class_ba_Widget">ba.Widget</a> = None, parent: <a href="#class_ba_Widget">ba.Widget</a> = None,
  size: Sequence[float] = None,
  position: Sequence[float] = None,
  background: bool = None, selected_child: <a href="#class_ba_Widget">ba.Widget</a> = None,
  visible_child: <a href="#class_ba_Widget">ba.Widget</a> = None,
  claims_left_right: bool = None,
  claims_tab: bool = None,
  selection_loops_to_parent: bool = None) -&gt; <a href="#class_ba_Widget">ba.Widget</a></span></p>

<p>Create or edit a row widget.</p>

<p>Category: <a href="#function_category_User_Interface_Functions">User Interface Functions</a></p>

<p>Pass a valid existing <a href="#class_ba_Widget">ba.Widget</a> as 'edit' to modify it; otherwise
a new one is created and returned. Arguments that are not set to None
are applied to the Widget.</p>

<hr>
<h2><strong><a name="function_ba_safecolor">ba.safecolor()</a></strong></h3>
<p><span>safecolor(color: Sequence[float], target_intensity: float = 0.6)
  -&gt; Tuple[float, ...]</span></p>

<p>Given a color tuple, return a color safe to display as text.</p>

<p>Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p>Accepts tuples of length 3 or 4. This will slightly brighten very
dark colors, etc.</p>

<hr>
<h2><strong><a name="function_ba_screenmessage">ba.screenmessage()</a></strong></h3>
<p><span>screenmessage(message: Union[str, <a href="#class_ba_Lstr">ba.Lstr</a>],
  color: Sequence[float] = None, top: bool = False,
  image: Dict[str, Any] = None, log: bool = False,
  clients: Sequence[int] = None, transient: bool = False) -&gt; None</span></p>

<p>Print a message to the local client's screen, in a given color.</p>

<p>Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p>If 'top' is True, the message will go to the top message area.
For 'top' messages, 'image' can be a texture to display alongside the
message.
If 'log' is True, the message will also be printed to the output log
'clients' can be a list of client-ids the message should be sent to,
or None to specify that everyone should receive it.
If 'transient' is True, the message will not be included in the
game-stream and thus will not show up when viewing replays.
Currently the 'clients' option only works for transient messages.</p>

<hr>
<h2><strong><a name="function_ba_scrollwidget">ba.scrollwidget()</a></strong></h3>
<p><span>scrollwidget(edit: <a href="#class_ba_Widget">ba.Widget</a> = None, parent: <a href="#class_ba_Widget">ba.Widget</a> = None,
  size: Sequence[float] = None, position: Sequence[float] = None,
  background: bool = None, selected_child: <a href="#class_ba_Widget">ba.Widget</a> = None,
  capture_arrows: bool = False, on_select_call: Callable = None,
  center_small_content: bool = None, color: Sequence[float] = None,
  highlight: bool = None, border_opacity: float = None,
  simple_culling_v: float = None,
  selection_loops_to_parent: bool = None,
  claims_left_right: bool = None,
  claims_up_down: bool = None,
  claims_tab: bool = None,
  autoselect: bool = None) -&gt; <a href="#class_ba_Widget">ba.Widget</a></span></p>

<p>Create or edit a scroll widget.</p>

<p>Category: <a href="#function_category_User_Interface_Functions">User Interface Functions</a></p>

<p>Pass a valid existing <a href="#class_ba_Widget">ba.Widget</a> as 'edit' to modify it; otherwise
a new one is created and returned. Arguments that are not set to None
are applied to the Widget.</p>

<hr>
<h2><strong><a name="function_ba_set_analytics_screen">ba.set_analytics_screen()</a></strong></h3>
<p><span>set_analytics_screen(screen: str) -&gt; None</span></p>

<p>Used for analytics to see where in the app players spend their time.</p>

<p>Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p>Generally called when opening a new window or entering some UI.
'screen' should be a string description of an app location
('Main Menu', etc.)</p>

<hr>
<h2><strong><a name="function_ba_setmusic">ba.setmusic()</a></strong></h3>
<p><span>setmusic(musictype: Optional[<a href="#class_ba_MusicType">ba.MusicType</a>], continuous: bool = False) -&gt; None</span></p>

<p>Set the app to play (or stop playing) a certain type of music.</p>

<p>Category: <a href="#function_category_Gameplay_Functions">Gameplay Functions</a></p>

<p>This function will handle loading and playing sound assets as necessary,
and also supports custom user soundtracks on specific platforms so the
user can override particular game music with their own.</p>

<p>Pass None to stop music.</p>

<p>if 'continuous' is True and musictype is the same as what is already
playing, the playing track will not be restarted.</p>

<hr>
<h2><strong><a name="function_ba_show_damage_count">ba.show_damage_count()</a></strong></h3>
<p><span>show_damage_count(damage: str, position: Sequence[float], direction: Sequence[float]) -&gt; None</span></p>

<p>Pop up a damage count at a position in space.</p>

<p>Category: <a href="#function_category_Gameplay_Functions">Gameplay Functions</a></p>

<hr>
<h2><strong><a name="function_ba_storagename">ba.storagename()</a></strong></h3>
<p><span>storagename(suffix: str = None) -&gt; str</span></p>

<p>Generate a unique name for storing class data in shared places.</p>

<p>Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p>This consists of a leading underscore, the module path at the
call site with dots replaced by underscores, the containing class's
qualified name, and the provided suffix. When storing data in public
places such as 'customdata' dicts, this minimizes the chance of
collisions with other similarly named classes.</p>

<p>Note that this will function even if called in the class definition.</p>

<pre><span><em><small># Example: generate a unique name for storage purposes:</small></em></span>
class MyThingie:</pre>

<pre><span><em><small>    # This will give something like '_mymodule_submodule_mythingie_data'.</small></em></span>
    _STORENAME = <a href="#function_ba_storagename">ba.storagename</a>('data')</pre>

<pre><span><em><small>    # Use that name to store some data in the Activity we were passed.</small></em></span>
    def __init__(self, activity):
        activity.customdata[self._STORENAME] = {}</pre>

<hr>
<h2><strong><a name="function_ba_textwidget">ba.textwidget()</a></strong></h3>
<p><span>textwidget(edit: <a href="#class_ba_Widget">ba.Widget</a> = None, parent: <a href="#class_ba_Widget">ba.Widget</a> = None,
  size: Sequence[float] = None, position: Sequence[float] = None,
  text: Union[str, <a href="#class_ba_Lstr">ba.Lstr</a>] = None, v_align: str = None,
  h_align: str = None, editable: bool = None, padding: float = None,
  on_return_press_call: Callable[[], None] = None,
  on_activate_call: Callable[[], None] = None,
  selectable: bool = None, query: <a href="#class_ba_Widget">ba.Widget</a> = None, max_chars: int = None,
  color: Sequence[float] = None, click_activate: bool = None,
  on_select_call: Callable[[], None] = None,
  always_highlight: bool = None, draw_controller: <a href="#class_ba_Widget">ba.Widget</a> = None,
  scale: float = None, corner_scale: float = None,
  description: Union[str, <a href="#class_ba_Lstr">ba.Lstr</a>] = None,
  transition_delay: float = None, maxwidth: float = None,
  max_height: float = None, flatness: float = None,
  shadow: float = None, autoselect: bool = None, rotate: float = None,
  enabled: bool = None, force_internal_editing: bool = None,
  always_show_carat: bool = None, big: bool = None,
  extra_touch_border_scale: float = None, res_scale: float = None)
  -&gt; Widget</span></p>

<p>Create or edit a text widget.</p>

<p>Category: <a href="#function_category_User_Interface_Functions">User Interface Functions</a></p>

<p>Pass a valid existing <a href="#class_ba_Widget">ba.Widget</a> as 'edit' to modify it; otherwise
a new one is created and returned. Arguments that are not set to None
are applied to the Widget.</p>

<hr>
<h2><strong><a name="function_ba_time">ba.time()</a></strong></h3>
<p><span>time(timetype: <a href="#class_ba_TimeType">ba.TimeType</a> = TimeType.SIM,
  timeformat: <a href="#class_ba_TimeFormat">ba.TimeFormat</a> = TimeFormat.SECONDS)
  -&gt; &lt;varies&gt;</span></p>

<p>Return the current time.</p>

<p>Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p>The time returned depends on the current <a href="#class_ba_Context">ba.Context</a> and timetype.</p>

<p>timetype can be either SIM, BASE, or REAL. It defaults to
SIM. Types are explained below:</p>

<p>SIM time maps to local simulation time in <a href="#class_ba_Activity">ba.Activity</a> or <a href="#class_ba_Session">ba.Session</a>
Contexts. This means that it may progress slower in slow-motion play
modes, stop when the game is paused, etc.  This time type is not
available in UI contexts.</p>

<p>BASE time is also linked to gameplay in <a href="#class_ba_Activity">ba.Activity</a> or <a href="#class_ba_Session">ba.Session</a>
Contexts, but it progresses at a constant rate regardless of
 slow-motion states or pausing.  It can, however, slow down or stop
in certain cases such as network outages or game slowdowns due to
cpu load. Like 'sim' time, this is unavailable in UI contexts.</p>

<p>REAL time always maps to actual clock time with a bit of filtering
added, regardless of Context.  (the filtering prevents it from going
backwards or jumping forward by large amounts due to the app being
backgrounded, system time changing, etc.)</p>

<p>the 'timeformat' arg defaults to SECONDS which returns float seconds,
but it can also be MILLISECONDS to return integer milliseconds.</p>

<p>Note: If you need pure unfiltered clock time, just use the standard
Python functions such as time.time().</p>

<hr>
<h2><strong><a name="function_ba_timer">ba.timer()</a></strong></h3>
<p><span>timer(time: float, call: Callable[[], Any], repeat: bool = False,
  timetype: <a href="#class_ba_TimeType">ba.TimeType</a> = TimeType.SIM,
  timeformat: <a href="#class_ba_TimeFormat">ba.TimeFormat</a> = TimeFormat.SECONDS,
  suppress_format_warning: bool = False)
 -&gt; None</span></p>

<p>Schedule a call to run at a later point in time.</p>

<p>Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p>This function adds a timer to the current <a href="#class_ba_Context">ba.Context</a>.
This timer cannot be canceled or modified once created. If you
 require the ability to do so, use the <a href="#class_ba_Timer">ba.Timer</a> class instead.</p>

<p>time: length of time (in seconds by default) that the timer will wait
before firing. Note that the actual delay experienced may vary
 depending on the timetype. (see below)</p>

<p>call: A callable Python object. Note that the timer will retain a
strong reference to the callable for as long as it exists, so you
may want to look into concepts such as <a href="#class_ba_WeakCall">ba.WeakCall</a> if that is not
desired.</p>

<p>repeat: if True, the timer will fire repeatedly, with each successive
firing having the same delay as the first.</p>

<p>timetype can be either 'sim', 'base', or 'real'. It defaults to
'sim'. Types are explained below:</p>

<p>'sim' time maps to local simulation time in <a href="#class_ba_Activity">ba.Activity</a> or <a href="#class_ba_Session">ba.Session</a>
Contexts. This means that it may progress slower in slow-motion play
modes, stop when the game is paused, etc.  This time type is not
available in UI contexts.</p>

<p>'base' time is also linked to gameplay in <a href="#class_ba_Activity">ba.Activity</a> or <a href="#class_ba_Session">ba.Session</a>
Contexts, but it progresses at a constant rate regardless of
 slow-motion states or pausing.  It can, however, slow down or stop
in certain cases such as network outages or game slowdowns due to
cpu load. Like 'sim' time, this is unavailable in UI contexts.</p>

<p>'real' time always maps to actual clock time with a bit of filtering
added, regardless of Context.  (the filtering prevents it from going
backwards or jumping forward by large amounts due to the app being
backgrounded, system time changing, etc.)
Real time timers are currently only available in the UI context.</p>

<p>the 'timeformat' arg defaults to seconds but can also be milliseconds.</p>

<pre><span><em><small># timer example: print some stuff through time:</small></em></span>
<a href="#function_ba_screenmessage">ba.screenmessage</a>('hello from now!')
<a href="#function_ba_timer">ba.timer</a>(1.0, <a href="#class_ba_Call">ba.Call</a>(<a href="#function_ba_screenmessage">ba.screenmessage</a>, 'hello from the future!'))
<a href="#function_ba_timer">ba.timer</a>(2.0, <a href="#class_ba_Call">ba.Call</a>(<a href="#function_ba_screenmessage">ba.screenmessage</a>, 'hello from the future 2!'))</pre>

<hr>
<h2><strong><a name="function_ba_timestring">ba.timestring()</a></strong></h3>
<p><span>timestring(timeval: float, centi: bool = True, timeformat: <a href="#class_ba_TimeFormat">ba.TimeFormat</a> = &lt;TimeFormat.SECONDS: 0&gt;, suppress_format_warning: bool = False) -&gt; <a href="#class_ba_Lstr">ba.Lstr</a></span></p>

<p>Generate a <a href="#class_ba_Lstr">ba.Lstr</a> for displaying a time value.</p>

<p>Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p>Given a time value, returns a <a href="#class_ba_Lstr">ba.Lstr</a> with:
(hours if &gt; 0 ) : minutes : seconds : (centiseconds if centi=True).</p>

<p>Time 'timeval' is specified in seconds by default, or 'timeformat' can
be set to <a href="#class_ba_TimeFormat">ba.TimeFormat</a>.MILLISECONDS to accept milliseconds instead.</p>

<p>WARNING: the underlying Lstr value is somewhat large so don't use this
to rapidly update Node text values for an onscreen timer or you may
consume significant network bandwidth.  For that purpose you should
use a 'timedisplay' Node and attribute connections.</p>

<hr>
<h2><strong><a name="function_ba_uicleanupcheck">ba.uicleanupcheck()</a></strong></h3>
<p><span>uicleanupcheck(obj: Any, widget: <a href="#class_ba_Widget">ba.Widget</a>) -&gt; None</span></p>

<p>Add a check to ensure a widget-owning object gets cleaned up properly.</p>

<p>Category: <a href="#function_category_User_Interface_Functions">User Interface Functions</a></p>

<p>This adds a check which will print an error message if the provided
object still exists ~5 seconds after the provided <a href="#class_ba_Widget">ba.Widget</a> dies.</p>

<p>This is a good sanity check for any sort of object that wraps or
controls a <a href="#class_ba_Widget">ba.Widget</a>. For instance, a 'Window' class instance has
no reason to still exist once its root container <a href="#class_ba_Widget">ba.Widget</a> has fully
transitioned out and been destroyed. Circular references or careless
strong referencing can lead to such objects never getting destroyed,
however, and this helps detect such cases to avoid memory leaks.</p>

<hr>
<h2><strong><a name="function_ba_vec3validate">ba.vec3validate()</a></strong></h3>
<p><span>vec3validate(value: Sequence[float]) -&gt; Sequence[float]</span></p>

<p>Ensure a value is valid for use as a Vec3.</p>

<p>Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p>Raises a TypeError exception if not.
Valid values include any type of sequence consisting of 3 numeric values.
Returns the same value as passed in (but with a definite type
so this can be used to disambiguate 'Any' types).
Generally this should be used in 'if __debug__' or assert clauses
to keep runtime overhead minimal.</p>

<hr>
<h2><strong><a name="function_ba_verify_object_death">ba.verify_object_death()</a></strong></h3>
<p><span>verify_object_death(obj: object) -&gt; None</span></p>

<p>Warn if an object does not get freed within a short period.</p>

<p>Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p>This can be handy to detect and prevent memory/resource leaks.</p>

<hr>
<h2><strong><a name="function_ba_widget">ba.widget()</a></strong></h3>
<p><span>widget(edit: <a href="#class_ba_Widget">ba.Widget</a> = None, up_widget: <a href="#class_ba_Widget">ba.Widget</a> = None,
  down_widget: <a href="#class_ba_Widget">ba.Widget</a> = None, left_widget: <a href="#class_ba_Widget">ba.Widget</a> = None,
  right_widget: <a href="#class_ba_Widget">ba.Widget</a> = None, show_buffer_top: float = None,
  show_buffer_bottom: float = None, show_buffer_left: float = None,
  show_buffer_right: float = None, autoselect: bool = None) -&gt; None</span></p>

<p>Edit common attributes of any widget.</p>

<p>Category: <a href="#function_category_User_Interface_Functions">User Interface Functions</a></p>

<p>Unlike other UI calls, this can only be used to edit, not to create.</p>

