<!-- THIS FILE IS AUTO GENERATED; DO NOT EDIT BY HAND -->
<!--DOCSHASH=aff21e829575f81236ae45ffa0ed1039-->
<h4><em>last updated on 2020-01-04 for Ballistica version 1.5.0 build 20001</em></h4>
<p>This page documents the Python classes and functions in the 'ba' module,
 which are the ones most relevant to modding in Ballistica. If you come across something you feel should be included here or could be better explained, please <a href="mailto:support@froemling.net">let me know</a>. Happy modding!</p>
<hr>
<h2>Table of Contents</h2>
<h4><a class="offsanchor" name="class_category_Gameplay_Classes">Gameplay Classes</a></h4>
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
   </ul>
   <li><a href="#class_ba_InputDevice">ba.InputDevice</a></li>
   <li><a href="#class_ba_Level">ba.Level</a></li>
   <li><a href="#class_ba_Material">ba.Material</a></li>
   <li><a href="#class_ba_Node">ba.Node</a></li>
   <li><a href="#class_ba_Player">ba.Player</a></li>
   <li><a href="#class_ba_PlayerRecord">ba.PlayerRecord</a></li>
   <li><a href="#class_ba_Session">ba.Session</a></li>
   <ul>
      <li><a href="#class_ba_CoopSession">ba.CoopSession</a></li>
      <li><a href="#class_ba_TeamBaseSession">ba.TeamBaseSession</a></li>
      <ul>
         <li><a href="#class_ba_FreeForAllSession">ba.FreeForAllSession</a></li>
         <li><a href="#class_ba_TeamsSession">ba.TeamsSession</a></li>
      </ul>
   </ul>
   <li><a href="#class_ba_Stats">ba.Stats</a></li>
   <li><a href="#class_ba_Team">ba.Team</a></li>
   <li><a href="#class_ba_TeamGameResults">ba.TeamGameResults</a></li>
</ul>
<h4><a class="offsanchor" name="function_category_Gameplay_Functions">Gameplay Functions</a></h4>
<ul>
   <li><a href="#function_ba_animate">ba.animate()</a></li>
   <li><a href="#function_ba_animate_array">ba.animate_array()</a></li>
   <li><a href="#function_ba_cameraflash">ba.cameraflash()</a></li>
   <li><a href="#function_ba_camerashake">ba.camerashake()</a></li>
   <li><a href="#function_ba_emitfx">ba.emitfx()</a></li>
   <li><a href="#function_ba_get_collision_info">ba.get_collision_info()</a></li>
   <li><a href="#function_ba_getactivity">ba.getactivity()</a></li>
   <li><a href="#function_ba_getnodes">ba.getnodes()</a></li>
   <li><a href="#function_ba_getsession">ba.getsession()</a></li>
   <li><a href="#function_ba_newnode">ba.newnode()</a></li>
   <li><a href="#function_ba_playsound">ba.playsound()</a></li>
   <li><a href="#function_ba_printnodes">ba.printnodes()</a></li>
   <li><a href="#function_ba_setmusic">ba.setmusic()</a></li>
   <li><a href="#function_ba_sharedobj">ba.sharedobj()</a></li>
</ul>
<h4><a class="offsanchor" name="class_category_General_Utility_Classes">General Utility Classes</a></h4>
<ul>
   <li><a href="#class_ba_App">ba.App</a></li>
   <li><a href="#class_ba_AppConfig">ba.AppConfig</a></li>
   <li><a href="#class_ba_Call">ba.Call</a></li>
   <li><a href="#class_ba_Context">ba.Context</a></li>
   <li><a href="#class_ba_ContextCall">ba.ContextCall</a></li>
   <li><a href="#class_ba_Lstr">ba.Lstr</a></li>
   <li><a href="#class_ba_Timer">ba.Timer</a></li>
   <li><a href="#class_ba_Vec3">ba.Vec3</a></li>
   <li><a href="#class_ba_WeakCall">ba.WeakCall</a></li>
</ul>
<h4><a class="offsanchor" name="function_category_General_Utility_Functions">General Utility Functions</a></h4>
<ul>
   <li><a href="#function_ba_charstr">ba.charstr()</a></li>
   <li><a href="#function_ba_do_once">ba.do_once()</a></li>
   <li><a href="#function_ba_get_valid_languages">ba.get_valid_languages()</a></li>
   <li><a href="#function_ba_is_browser_likely_available">ba.is_browser_likely_available()</a></li>
   <li><a href="#function_ba_is_point_in_box">ba.is_point_in_box()</a></li>
   <li><a href="#function_ba_log">ba.log()</a></li>
   <li><a href="#function_ba_new_activity">ba.new_activity()</a></li>
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
   <li><a href="#function_ba_setlanguage">ba.setlanguage()</a></li>
   <li><a href="#function_ba_time">ba.time()</a></li>
   <li><a href="#function_ba_timer">ba.timer()</a></li>
   <li><a href="#function_ba_timestring">ba.timestring()</a></li>
   <li><a href="#function_ba_vec3validate">ba.vec3validate()</a></li>
</ul>
<h4><a class="offsanchor" name="class_category_Asset_Classes">Asset Classes</a></h4>
<ul>
   <li><a href="#class_ba_CollideModel">ba.CollideModel</a></li>
   <li><a href="#class_ba_Data">ba.Data</a></li>
   <li><a href="#class_ba_Model">ba.Model</a></li>
   <li><a href="#class_ba_Sound">ba.Sound</a></li>
   <li><a href="#class_ba_Texture">ba.Texture</a></li>
</ul>
<h4><a class="offsanchor" name="function_category_Asset_Functions">Asset Functions</a></h4>
<ul>
   <li><a href="#function_ba_getcollidemodel">ba.getcollidemodel()</a></li>
   <li><a href="#function_ba_getmaps">ba.getmaps()</a></li>
   <li><a href="#function_ba_getmodel">ba.getmodel()</a></li>
   <li><a href="#function_ba_getsound">ba.getsound()</a></li>
   <li><a href="#function_ba_gettexture">ba.gettexture()</a></li>
</ul>
<h4><a class="offsanchor" name="class_category_Message_Classes">Message Classes</a></h4>
<ul>
   <li><a href="#class_ba_DieMessage">ba.DieMessage</a></li>
   <li><a href="#class_ba_DropMessage">ba.DropMessage</a></li>
   <li><a href="#class_ba_DroppedMessage">ba.DroppedMessage</a></li>
   <li><a href="#class_ba_FreezeMessage">ba.FreezeMessage</a></li>
   <li><a href="#class_ba_HitMessage">ba.HitMessage</a></li>
   <li><a href="#class_ba_ImpactDamageMessage">ba.ImpactDamageMessage</a></li>
   <li><a href="#class_ba_OutOfBoundsMessage">ba.OutOfBoundsMessage</a></li>
   <li><a href="#class_ba_PickedUpMessage">ba.PickedUpMessage</a></li>
   <li><a href="#class_ba_PickUpMessage">ba.PickUpMessage</a></li>
   <li><a href="#class_ba_PlayerScoredMessage">ba.PlayerScoredMessage</a></li>
   <li><a href="#class_ba_PowerupAcceptMessage">ba.PowerupAcceptMessage</a></li>
   <li><a href="#class_ba_PowerupMessage">ba.PowerupMessage</a></li>
   <li><a href="#class_ba_ShouldShatterMessage">ba.ShouldShatterMessage</a></li>
   <li><a href="#class_ba_StandMessage">ba.StandMessage</a></li>
   <li><a href="#class_ba_ThawMessage">ba.ThawMessage</a></li>
</ul>
<h4><a class="offsanchor" name="class_category_User_Interface_Classes">User Interface Classes</a></h4>
<ul>
   <li><a href="#class_ba_UILocation">ba.UILocation</a></li>
   <ul>
      <li><a href="#class_ba_UILocationWindow">ba.UILocationWindow</a></li>
   </ul>
   <li><a href="#class_ba_Widget">ba.Widget</a></li>
</ul>
<h4><a class="offsanchor" name="function_category_User_Interface_Functions">User Interface Functions</a></h4>
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
<h4><a class="offsanchor" name="class_category_Dependency_Classes">Dependency Classes</a></h4>
<ul>
   <li><a href="#class_ba_Dependency">ba.Dependency</a></li>
   <li><a href="#class_ba_DependencyComponent">ba.DependencyComponent</a></li>
</ul>
<h4><a class="offsanchor" name="class_category_Enums">Enums</a></h4>
<ul>
   <li><a href="#class_ba_Permission">ba.Permission</a></li>
   <li><a href="#class_ba_SpecialChar">ba.SpecialChar</a></li>
   <li><a href="#class_ba_TimeFormat">ba.TimeFormat</a></li>
   <li><a href="#class_ba_TimeType">ba.TimeType</a></li>
</ul>
<h4><a class="offsanchor" name="class_category_Exception_Classes">Exception Classes</a></h4>
<ul>
   <li><a href="#class_ba_DependencyError">ba.DependencyError</a></li>
   <li><a href="#class_ba_NotFoundError">ba.NotFoundError</a></li>
   <ul>
      <li><a href="#class_ba_ActivityNotFoundError">ba.ActivityNotFoundError</a></li>
      <li><a href="#class_ba_ActorNotFoundError">ba.ActorNotFoundError</a></li>
      <li><a href="#class_ba_InputDeviceNotFoundError">ba.InputDeviceNotFoundError</a></li>
      <li><a href="#class_ba_NodeNotFoundError">ba.NodeNotFoundError</a></li>
      <li><a href="#class_ba_PlayerNotFoundError">ba.PlayerNotFoundError</a></li>
      <li><a href="#class_ba_SessionNotFoundError">ba.SessionNotFoundError</a></li>
      <li><a href="#class_ba_TeamNotFoundError">ba.TeamNotFoundError</a></li>
      <li><a href="#class_ba_WidgetNotFoundError">ba.WidgetNotFoundError</a></li>
   </ul>
</ul>
<h4><a class="offsanchor" name="class_category_Misc">Misc</a></h4>
<ul>
   <li><a href="#class_ba_Achievement">ba.Achievement</a></li>
   <li><a href="#class_ba_AppDelegate">ba.AppDelegate</a></li>
   <li><a href="#class_ba_AssetPackage">ba.AssetPackage</a></li>
   <li><a href="#class_ba_Campaign">ba.Campaign</a></li>
   <li><a href="#class_ba_Chooser">ba.Chooser</a></li>
   <li><a href="#class_ba_DependencySet">ba.DependencySet</a></li>
   <li><a href="#class_ba_Lobby">ba.Lobby</a></li>
   <li><a href="#class_ba_MusicPlayer">ba.MusicPlayer</a></li>
   <li><a href="#class_ba_OldWindow">ba.OldWindow</a></li>
   <li><a href="#class_ba_UIController">ba.UIController</a></li>
</ul>
<h4><a class="offsanchor" name="function_category_Misc">Misc</a></h4>
<ul>
   <li><a href="#function_ba_show_damage_count">ba.show_damage_count()</a></li>
</ul>
<hr>
<h2><strong><a class="offsanchor" name="class_ba_Achievement">ba.Achievement</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">Represents attributes and state for an individual achievement.</p>

<h3 style="padding-left: 0px;">Attributes:</h3>
<h5 style="padding-left: 30px;"><a href="#attr_ba_Achievement__complete">complete</a>, <a href="#attr_ba_Achievement__description">description</a>, <a href="#attr_ba_Achievement__description_complete">description_complete</a>, <a href="#attr_ba_Achievement__description_full">description_full</a>, <a href="#attr_ba_Achievement__description_full_complete">description_full_complete</a>, <a href="#attr_ba_Achievement__display_name">display_name</a>, <a href="#attr_ba_Achievement__hard_mode_only">hard_mode_only</a>, <a href="#attr_ba_Achievement__level_name">level_name</a>, <a href="#attr_ba_Achievement__name">name</a>, <a href="#attr_ba_Achievement__power_ranking_value">power_ranking_value</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Achievement__complete"><strong>complete</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">bool</span></p>
<p style="padding-left: 60px;">Whether this Achievement is currently complete.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Achievement__description"><strong>description</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"><a href="#class_ba_Lstr">ba.Lstr</a></span></p>
<p style="padding-left: 60px;">Get a <a href="#class_ba_Lstr">ba.Lstr</a> for the Achievement's brief description.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Achievement__description_complete"><strong>description_complete</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"><a href="#class_ba_Lstr">ba.Lstr</a></span></p>
<p style="padding-left: 60px;">Get a <a href="#class_ba_Lstr">ba.Lstr</a> for the Achievement's description when completed.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Achievement__description_full"><strong>description_full</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"><a href="#class_ba_Lstr">ba.Lstr</a></span></p>
<p style="padding-left: 60px;">Get a <a href="#class_ba_Lstr">ba.Lstr</a> for the Achievement's full description.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Achievement__description_full_complete"><strong>description_full_complete</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"><a href="#class_ba_Lstr">ba.Lstr</a></span></p>
<p style="padding-left: 60px;">Get a <a href="#class_ba_Lstr">ba.Lstr</a> for the Achievement's full desc. when completed.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Achievement__display_name"><strong>display_name</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"><a href="#class_ba_Lstr">ba.Lstr</a></span></p>
<p style="padding-left: 60px;">Return a <a href="#class_ba_Lstr">ba.Lstr</a> for this Achievement's name.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Achievement__hard_mode_only"><strong>hard_mode_only</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">bool</span></p>
<p style="padding-left: 60px;">Whether this Achievement is only unlockable in hard-mode.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Achievement__level_name"><strong>level_name</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">str</span></p>
<p style="padding-left: 60px;">The name of the level this achievement applies to.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Achievement__name"><strong>name</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">str</span></p>
<p style="padding-left: 60px;">The name of this achievement.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Achievement__power_ranking_value"><strong>power_ranking_value</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">int</span></p>
<p style="padding-left: 60px;">Get the power-ranking award value for this achievement.</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_Achievement____init__">&lt;constructor&gt;</a>, <a href="#method_ba_Achievement__announce_completion">announce_completion()</a>, <a href="#method_ba_Achievement__create_display">create_display()</a>, <a href="#method_ba_Achievement__get_award_ticket_value">get_award_ticket_value()</a>, <a href="#method_ba_Achievement__get_icon_color">get_icon_color()</a>, <a href="#method_ba_Achievement__get_icon_texture">get_icon_texture()</a>, <a href="#method_ba_Achievement__set_complete">set_complete()</a>, <a href="#method_ba_Achievement__show_completion_banner">show_completion_banner()</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Achievement____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.Achievement(name: str, icon_name: str, icon_color: Sequence[float], level_name: str, award: int, hard_mode_only: bool = False)</span></p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Achievement__announce_completion"><strong>announce_completion()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">announce_completion(self, sound: bool = True) -&gt; None</span></p>

<p style="padding-left: 60px;">Kick off an announcement for this achievement's completion.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Achievement__create_display"><strong>create_display()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">create_display(self, x: 'float', y: 'float', delay: 'float', outdelay: 'float' = None, color: 'Sequence[float]' = None, style: 'str' = 'post_game') -&gt; 'List[<a href="#class_ba_Actor">ba.Actor</a>]'</span></p>

<p style="padding-left: 60px;">Create a display for the Achievement.</p>

<p style="padding-left: 60px;">Shows the Achievement icon, name, and description.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Achievement__get_award_ticket_value"><strong>get_award_ticket_value()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_award_ticket_value(self, include_pro_bonus: bool = False) -&gt; int</span></p>

<p style="padding-left: 60px;">Get the ticket award value for this achievement.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Achievement__get_icon_color"><strong>get_icon_color()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_icon_color(self, complete: bool) -&gt; Sequence[float]</span></p>

<p style="padding-left: 60px;">Return the color tint for this Achievement's icon.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Achievement__get_icon_texture"><strong>get_icon_texture()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_icon_texture(self, complete: bool) -&gt; <a href="#class_ba_Texture">ba.Texture</a></span></p>

<p style="padding-left: 60px;">Return the icon texture to display for this achievement</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Achievement__set_complete"><strong>set_complete()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">set_complete(self, complete: bool = True) -&gt; None</span></p>

<p style="padding-left: 60px;">Set an achievement's completed state.</p>

<p style="padding-left: 60px;">note this only sets local state; use a transaction to
actually award achievements.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Achievement__show_completion_banner"><strong>show_completion_banner()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">show_completion_banner(self, sound: bool = True) -&gt; None</span></p>

<p style="padding-left: 60px;">Create the banner/sound for an acquired achievement announcement.</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_Activity">ba.Activity</a></strong></h3>
<p style="padding-left: 30px;">inherits from: <a href="#class_ba_DependencyComponent">ba.DependencyComponent</a></p>
<p style="padding-left: 30px;">Units of execution wrangled by a <a href="#class_ba_Session">ba.Session</a>.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a></p>

<p style="padding-left: 30px;">    Examples of Activities include games, score-screens, cutscenes, etc.
    A <a href="#class_ba_Session">ba.Session</a> has one 'current' Activity at any time, though their existence
    can overlap during transitions.</p>

<h3 style="padding-left: 0px;">Attributes:</h3>
<h5 style="padding-left: 30px;"><a href="#attr_ba_Activity__players">players</a>, <a href="#attr_ba_Activity__session">session</a>, <a href="#attr_ba_Activity__settings">settings</a>, <a href="#attr_ba_Activity__stats">stats</a>, <a href="#attr_ba_Activity__teams">teams</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Activity__players"><strong>players</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">List[_<a href="#class_ba_Player">ba.Player</a>]</span></p>
<p style="padding-left: 60px;">The list of <a href="#class_ba_Player">ba.Players</a> in the Activity. This gets populated just
before on_begin() is called and is updated automatically as players
join or leave the game.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Activity__session"><strong>session</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"><a href="#class_ba_Session">ba.Session</a></span></p>
<p style="padding-left: 60px;">The <a href="#class_ba_Session">ba.Session</a> this <a href="#class_ba_Activity">ba.Activity</a> belongs go.</p>

<p style="padding-left: 60px;">        Raises a <a href="#class_ba_SessionNotFoundError">ba.SessionNotFoundError</a> if the Session no longer exists.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Activity__settings"><strong>settings</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">Dict[str, Any]</span></p>
<p style="padding-left: 60px;">The settings dict passed in when the activity was made.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Activity__stats"><strong>stats</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"><a href="#class_ba_Stats">ba.Stats</a></span></p>
<p style="padding-left: 60px;">The stats instance accessible while the activity is running.</p>

<p style="padding-left: 60px;">        If access is attempted before or after, raises a <a href="#class_ba_NotFoundError">ba.NotFoundError</a>.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Activity__teams"><strong>teams</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">List[<a href="#class_ba_Team">ba.Team</a>]</span></p>
<p style="padding-left: 60px;">The list of <a href="#class_ba_Team">ba.Teams</a> in the Activity. This gets populated just before
before on_begin() is called and is updated automatically as players
join or leave the game. (at least in free-for-all mode where every
player gets their own team; in teams mode there are always 2 teams
regardless of the player count).</p>

<h3 style="padding-left: 0px;">Methods Inherited:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_DependencyComponent__dep_is_present">dep_is_present()</a>, <a href="#method_ba_DependencyComponent__get_dynamic_deps">get_dynamic_deps()</a></h5>
<h3 style="padding-left: 0px;">Methods Defined or Overridden:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_Activity____init__">&lt;constructor&gt;</a>, <a href="#method_ba_Activity__add_actor_weak_ref">add_actor_weak_ref()</a>, <a href="#method_ba_Activity__create_player_node">create_player_node()</a>, <a href="#method_ba_Activity__end">end()</a>, <a href="#method_ba_Activity__handlemessage">handlemessage()</a>, <a href="#method_ba_Activity__has_begun">has_begun()</a>, <a href="#method_ba_Activity__has_ended">has_ended()</a>, <a href="#method_ba_Activity__has_transitioned_in">has_transitioned_in()</a>, <a href="#method_ba_Activity__is_expired">is_expired()</a>, <a href="#method_ba_Activity__is_transitioning_out">is_transitioning_out()</a>, <a href="#method_ba_Activity__on_begin">on_begin()</a>, <a href="#method_ba_Activity__on_expire">on_expire()</a>, <a href="#method_ba_Activity__on_player_join">on_player_join()</a>, <a href="#method_ba_Activity__on_player_leave">on_player_leave()</a>, <a href="#method_ba_Activity__on_team_join">on_team_join()</a>, <a href="#method_ba_Activity__on_team_leave">on_team_leave()</a>, <a href="#method_ba_Activity__on_transition_in">on_transition_in()</a>, <a href="#method_ba_Activity__on_transition_out">on_transition_out()</a>, <a href="#method_ba_Activity__retain_actor">retain_actor()</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Activity____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.Activity(settings: Dict[str, Any])</span></p>

<p style="padding-left: 60px;">Creates an activity in the current <a href="#class_ba_Session">ba.Session</a>.</p>

<p style="padding-left: 60px;">The activity will not be actually run until <a href="#method_ba_Session__set_activity">ba.Session.set_activity</a>()
is called. 'settings' should be a dict of key/value pairs specific
to the activity.</p>

<p style="padding-left: 60px;">Activities should preload as much of their media/etc as possible in
their constructor, but none of it should actually be used until they
are transitioned in.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Activity__add_actor_weak_ref"><strong>add_actor_weak_ref()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">add_actor_weak_ref(self, actor: <a href="#class_ba_Actor">ba.Actor</a>) -&gt; None</span></p>

<p style="padding-left: 60px;">Add a weak-reference to a <a href="#class_ba_Actor">ba.Actor</a> to the <a href="#class_ba_Activity">ba.Activity</a>.</p>

<p style="padding-left: 60px;">(called by the <a href="#class_ba_Actor">ba.Actor</a> base class)</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Activity__create_player_node"><strong>create_player_node()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">create_player_node(self, player: <a href="#class_ba_Player">ba.Player</a>) -&gt; <a href="#class_ba_Node">ba.Node</a></span></p>

<p style="padding-left: 60px;">Create the 'player' node associated with the provided <a href="#class_ba_Player">ba.Player</a>.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Activity__end"><strong>end()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">end(self, results: Any = None, delay: float = 0.0, force: bool = False) -&gt; None</span></p>

<p style="padding-left: 60px;">Commences Activity shutdown and delivers results to the <a href="#class_ba_Session">ba.Session</a>.</p>

<p style="padding-left: 60px;">'delay' is the time delay before the Activity actually ends
(in seconds). Further calls to end() will be ignored up until
this time, unless 'force' is True, in which case the new results
will replace the old.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Activity__handlemessage"><strong>handlemessage()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">handlemessage(self, msg: Any) -&gt; Any</span></p>

<p style="padding-left: 60px;">General message handling; can be passed any <a href="#class_category_Message_Classes">message object</a>.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Activity__has_begun"><strong>has_begun()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">has_begun(self) -&gt; bool</span></p>

<p style="padding-left: 60px;">Return whether on_begin() has been called.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Activity__has_ended"><strong>has_ended()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">has_ended(self) -&gt; bool</span></p>

<p style="padding-left: 60px;">Return whether the activity has commenced ending.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Activity__has_transitioned_in"><strong>has_transitioned_in()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">has_transitioned_in(self) -&gt; bool</span></p>

<p style="padding-left: 60px;">Return whether on_transition_in() has been called.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Activity__is_expired"><strong>is_expired()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">is_expired(self) -&gt; bool</span></p>

<p style="padding-left: 60px;">Return whether the activity is expired.</p>

<p style="padding-left: 60px;">An activity is set as expired when shutting down.
At this point no new nodes, timers, etc should be made,
run, etc, and the activity should be considered a 'zombie'.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Activity__is_transitioning_out"><strong>is_transitioning_out()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">is_transitioning_out(self) -&gt; bool</span></p>

<p style="padding-left: 60px;">Return whether on_transition_out() has been called.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Activity__on_begin"><strong>on_begin()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">on_begin(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Called once the previous <a href="#class_ba_Activity">ba.Activity</a> has finished transitioning out.</p>

<p style="padding-left: 60px;">At this point the activity's initial players and teams are filled in
and it should begin its actual game logic.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Activity__on_expire"><strong>on_expire()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">on_expire(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Called when your activity is being expired.</p>

<p style="padding-left: 60px;">If your activity has created anything explicitly that may be retaining
a strong reference to the activity and preventing it from dying, you
should clear that out here. From this point on your activity's sole
purpose in life is to hit zero references and die so the next activity
can begin.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Activity__on_player_join"><strong>on_player_join()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">on_player_join(self, player: <a href="#class_ba_Player">ba.Player</a>) -&gt; None</span></p>

<p style="padding-left: 60px;">Called when a new <a href="#class_ba_Player">ba.Player</a> has joined the Activity.</p>

<p style="padding-left: 60px;">(including the initial set of Players)</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Activity__on_player_leave"><strong>on_player_leave()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">on_player_leave(self, player: <a href="#class_ba_Player">ba.Player</a>) -&gt; None</span></p>

<p style="padding-left: 60px;">Called when a <a href="#class_ba_Player">ba.Player</a> is leaving the Activity.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Activity__on_team_join"><strong>on_team_join()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">on_team_join(self, team: <a href="#class_ba_Team">ba.Team</a>) -&gt; None</span></p>

<p style="padding-left: 60px;">Called when a new <a href="#class_ba_Team">ba.Team</a> joins the Activity.</p>

<p style="padding-left: 60px;">(including the initial set of Teams)</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Activity__on_team_leave"><strong>on_team_leave()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">on_team_leave(self, team: <a href="#class_ba_Team">ba.Team</a>) -&gt; None</span></p>

<p style="padding-left: 60px;">Called when a <a href="#class_ba_Team">ba.Team</a> leaves the Activity.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Activity__on_transition_in"><strong>on_transition_in()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">on_transition_in(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Called when the Activity is first becoming visible.</p>

<p style="padding-left: 60px;">Upon this call, the Activity should fade in backgrounds,
start playing music, etc. It does not yet have access to <a href="#class_ba_Player">ba.Players</a>
or <a href="#class_ba_Team">ba.Teams</a>, however. They remain owned by the previous Activity
up until <a href="#method_ba_Activity__on_begin">ba.Activity.on_begin</a>() is called.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Activity__on_transition_out"><strong>on_transition_out()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">on_transition_out(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Called when your activity begins transitioning out.</p>

<p style="padding-left: 60px;">Note that this may happen at any time even if finish() has not been
called.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Activity__retain_actor"><strong>retain_actor()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">retain_actor(self, actor: <a href="#class_ba_Actor">ba.Actor</a>) -&gt; None</span></p>

<p style="padding-left: 60px;">Add a strong-reference to a <a href="#class_ba_Actor">ba.Actor</a> to this Activity.</p>

<p style="padding-left: 60px;">The reference will be lazily released once <a href="#method_ba_Actor__exists">ba.Actor.exists</a>()
returns False for the Actor. The <a href="#method_ba_Actor__autoretain">ba.Actor.autoretain</a>() method
is a convenient way to access this same functionality.</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_ActivityNotFoundError">ba.ActivityNotFoundError</a></strong></h3>
<p style="padding-left: 30px;">inherits from: <a href="#class_ba_NotFoundError">ba.NotFoundError</a>, Exception, BaseException</p>
<p style="padding-left: 30px;">Exception raised when an expected <a href="#class_ba_Activity">ba.Activity</a> does not exist.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Exception_Classes">Exception Classes</a>
</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<p style="padding-left: 30px;">&lt;all methods inherited from <a href="#class_ba_NotFoundError">ba.NotFoundError</a>&gt;</p>
<hr>
<h2><strong><a class="offsanchor" name="class_ba_Actor">ba.Actor</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">High level logical entities in a game/activity.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a></p>

<p style="padding-left: 30px;">    Actors act as controllers, combining some number of <a href="#class_ba_Node">ba.Nodes</a>,
    <a href="#class_ba_Texture">ba.Textures</a>, <a href="#class_ba_Sound">ba.Sounds</a>, etc. into one cohesive unit.</p>

<p style="padding-left: 30px;">    Some example actors include ba.Bomb, ba.Flag, and ba.Spaz.</p>

<p style="padding-left: 30px;">    One key feature of Actors is that they generally 'die'
    (killing off or transitioning out their nodes) when the last Python
    reference to them disappears, so you can use logic such as:</p>

<pre style="padding-left: 30px;"><span style="color: #008800;">    # create a flag Actor in our game activity</span>
    self.flag = ba.Flag(position=(0, 10, 0))</pre>

<pre style="padding-left: 30px;"><span style="color: #008800;">    # later, destroy the flag..</span>
<span style="color: #008800;">    # (provided nothing else is holding a reference to it)</span>
<span style="color: #008800;">    # we could also just assign a new flag to this value.</span>
<span style="color: #008800;">    # either way, the old flag disappears.</span>
    self.flag = None</pre>

<p style="padding-left: 30px;">    This is in contrast to the behavior of the more low level <a href="#class_ba_Node">ba.Nodes</a>,
    which are always explicitly created and destroyed and don't care
    how many Python references to them exist.</p>

<p style="padding-left: 30px;">    Note, however, that you can use the <a href="#method_ba_Actor__autoretain">ba.Actor.autoretain</a>() method
    if you want an Actor to stick around until explicitly killed
    regardless of references.</p>

<p style="padding-left: 30px;">    Another key feature of <a href="#class_ba_Actor">ba.Actor</a> is its handlemessage() method, which
    takes a single arbitrary object as an argument. This provides a safe way
    to communicate between <a href="#class_ba_Actor">ba.Actor</a>, <a href="#class_ba_Activity">ba.Activity</a>, <a href="#class_ba_Session">ba.Session</a>, and any other
    class providing a handlemessage() method.  The most universally handled
    message type for actors is the <a href="#class_ba_DieMessage">ba.DieMessage</a>.</p>

<pre style="padding-left: 30px;"><span style="color: #008800;">    # another way to kill the flag from the example above:</span>
<span style="color: #008800;">    # we can safely call this on any type with a 'handlemessage' method</span>
<span style="color: #008800;">    # (though its not guaranteed to always have a meaningful effect)</span>
<span style="color: #008800;">    # in this case the Actor instance will still be around, but its exists()</span>
<span style="color: #008800;">    # and is_alive() methods will both return False</span>
    self.flag.handlemessage(<a href="#class_ba_DieMessage">ba.DieMessage</a>())
</pre>

<h3 style="padding-left: 0px;">Attributes:</h3>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Actor__activity"><strong>activity</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"><a href="#class_ba_Activity">ba.Activity</a></span></p>
<p style="padding-left: 60px;">The Activity this Actor was created in.</p>

<p style="padding-left: 60px;">        Raises a <a href="#class_ba_ActivityNotFoundError">ba.ActivityNotFoundError</a> if the Activity no longer exists.</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_Actor____init__">&lt;constructor&gt;</a>, <a href="#method_ba_Actor__autoretain">autoretain()</a>, <a href="#method_ba_Actor__exists">exists()</a>, <a href="#method_ba_Actor__getactivity">getactivity()</a>, <a href="#method_ba_Actor__handlemessage">handlemessage()</a>, <a href="#method_ba_Actor__is_alive">is_alive()</a>, <a href="#method_ba_Actor__is_expired">is_expired()</a>, <a href="#method_ba_Actor__on_expire">on_expire()</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Actor____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.Actor(node: <a href="#class_ba_Node">ba.Node</a> = None)</span></p>

<p style="padding-left: 60px;">Instantiates an Actor in the current <a href="#class_ba_Activity">ba.Activity</a>.</p>

<p style="padding-left: 60px;">If 'node' is provided, it is stored as the 'node' attribute
and the default <a href="#method_ba_Actor__handlemessage">ba.Actor.handlemessage</a>() and <a href="#method_ba_Actor__exists">ba.Actor.exists</a>()
implementations will apply to it. This allows the creation of
simple node-wrapping Actors without having to create a new subclass.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Actor__autoretain"><strong>autoretain()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">autoretain(self: T) -&gt; T</span></p>

<p style="padding-left: 60px;">Keep this Actor alive without needing to hold a reference to it.</p>

<p style="padding-left: 60px;">This keeps the <a href="#class_ba_Actor">ba.Actor</a> in existence by storing a reference to it
with the <a href="#class_ba_Activity">ba.Activity</a> it was created in. The reference is lazily
released once <a href="#method_ba_Actor__exists">ba.Actor.exists</a>() returns False for it or when the
Activity is set as expired.  This can be a convenient alternative
to storing references explicitly just to keep a <a href="#class_ba_Actor">ba.Actor</a> from dying.
For convenience, this method returns the <a href="#class_ba_Actor">ba.Actor</a> it is called with,
enabling chained statements such as:  myflag = ba.Flag().autoretain()</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Actor__exists"><strong>exists()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">exists(self) -&gt; bool</span></p>

<p style="padding-left: 60px;">Returns whether the Actor is still present in a meaningful way.</p>

<p style="padding-left: 60px;">Note that a dying character should still return True here as long as
their corpse is visible; this is about presence, not being 'alive'
(see <a href="#method_ba_Actor__is_alive">ba.Actor.is_alive</a>() for that).</p>

<p style="padding-left: 60px;">If this returns False, it is assumed the Actor can be completely
deleted without affecting the game; this call is often used
when pruning lists of Actors, such as with <a href="#method_ba_Actor__autoretain">ba.Actor.autoretain</a>()</p>

<p style="padding-left: 60px;">The default implementation of this method returns 'node.exists()'
if the Actor has a 'node' attr; otherwise True.</p>

<p style="padding-left: 60px;">Note that the boolean operator for the Actor class calls this method,
so a simple "if myactor" test will conveniently do the right thing
even if myactor is set to None.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Actor__getactivity"><strong>getactivity()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">getactivity(self, doraise: bool = True) -&gt; Optional[<a href="#class_ba_Activity">ba.Activity</a>]</span></p>

<p style="padding-left: 60px;">Return the <a href="#class_ba_Activity">ba.Activity</a> this Actor is associated with.</p>

<p style="padding-left: 60px;">If the Activity no longer exists, raises a <a href="#class_ba_ActivityNotFoundError">ba.ActivityNotFoundError</a>
or returns None depending on whether 'doraise' is set.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Actor__handlemessage"><strong>handlemessage()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">handlemessage(self, msg: Any) -&gt; Any</span></p>

<p style="padding-left: 60px;">General message handling; can be passed any <a href="#class_category_Message_Classes">message object</a>.</p>

<p style="padding-left: 60px;">The default implementation will handle <a href="#class_ba_DieMessage">ba.DieMessages</a> by
calling self.node.delete() if self contains a 'node' attribute.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Actor__is_alive"><strong>is_alive()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">is_alive(self) -&gt; bool</span></p>

<p style="padding-left: 60px;">Returns whether the Actor is 'alive'.</p>

<p style="padding-left: 60px;">What this means is up to the Actor.
It is not a requirement for Actors to be
able to die; just that they report whether
they are Alive or not.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Actor__is_expired"><strong>is_expired()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">is_expired(self) -&gt; bool</span></p>

<p style="padding-left: 60px;">Returns whether the Actor is expired.</p>

<p style="padding-left: 60px;">(see <a href="#method_ba_Actor__on_expire">ba.Actor.on_expire</a>())</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Actor__on_expire"><strong>on_expire()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">on_expire(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Called for remaining <a href="#class_ba_Actor">ba.Actors</a> when their <a href="#class_ba_Activity">ba.Activity</a> shuts down.</p>

<p style="padding-left: 60px;">Actors can use this opportunity to clear callbacks
or other references which have the potential of keeping the
<a href="#class_ba_Activity">ba.Activity</a> alive inadvertently (Activities can not exit cleanly while
any Python references to them remain.)</p>

<p style="padding-left: 60px;">Once an actor is expired (see <a href="#method_ba_Actor__is_expired">ba.Actor.is_expired</a>()) it should no
longer perform any game-affecting operations (creating, modifying,
or deleting nodes, media, timers, etc.) Attempts to do so will
likely result in errors.</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_ActorNotFoundError">ba.ActorNotFoundError</a></strong></h3>
<p style="padding-left: 30px;">inherits from: <a href="#class_ba_NotFoundError">ba.NotFoundError</a>, Exception, BaseException</p>
<p style="padding-left: 30px;">Exception raised when an expected <a href="#class_ba_Actor">ba.Actor</a> does not exist.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Exception_Classes">Exception Classes</a>
</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<p style="padding-left: 30px;">&lt;all methods inherited from <a href="#class_ba_NotFoundError">ba.NotFoundError</a>&gt;</p>
<hr>
<h2><strong><a class="offsanchor" name="class_ba_App">ba.App</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">A class for high level app functionality and state.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_General_Utility_Classes">General Utility Classes</a></p>

<p style="padding-left: 30px;">    Use ba.app to access the single shared instance of this class.</p>

<p style="padding-left: 30px;">    Note that properties not documented here should be considered internal
    and subject to change without warning.
</p>

<h3 style="padding-left: 0px;">Attributes:</h3>
<h5 style="padding-left: 30px;"><a href="#attr_ba_App__build_number">build_number</a>, <a href="#attr_ba_App__config">config</a>, <a href="#attr_ba_App__config_file_path">config_file_path</a>, <a href="#attr_ba_App__debug_build">debug_build</a>, <a href="#attr_ba_App__interface_type">interface_type</a>, <a href="#attr_ba_App__language">language</a>, <a href="#attr_ba_App__locale">locale</a>, <a href="#attr_ba_App__on_tv">on_tv</a>, <a href="#attr_ba_App__platform">platform</a>, <a href="#attr_ba_App__subplatform">subplatform</a>, <a href="#attr_ba_App__system_scripts_directory">system_scripts_directory</a>, <a href="#attr_ba_App__test_build">test_build</a>, <a href="#attr_ba_App__ui_bounds">ui_bounds</a>, <a href="#attr_ba_App__user_agent_string">user_agent_string</a>, <a href="#attr_ba_App__user_scripts_directory">user_scripts_directory</a>, <a href="#attr_ba_App__version">version</a>, <a href="#attr_ba_App__vr_mode">vr_mode</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_App__build_number"><strong>build_number</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">int</span></p>
<p style="padding-left: 60px;">Integer build number.</p>

<p style="padding-left: 60px;">        This value increases by at least 1 with each release of the game.
        It is independent of the human readable <a href="#attr_ba_App__version">ba.App.version</a> string.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_App__config"><strong>config</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"><a href="#class_ba_AppConfig">ba.AppConfig</a></span></p>
<p style="padding-left: 60px;">The <a href="#class_ba_AppConfig">ba.AppConfig</a> instance representing the app's config state.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_App__config_file_path"><strong>config_file_path</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">str</span></p>
<p style="padding-left: 60px;">Where the game's config file is stored on disk.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_App__debug_build"><strong>debug_build</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">bool</span></p>
<p style="padding-left: 60px;">Whether the game was compiled in debug mode.</p>

<p style="padding-left: 60px;">        Debug builds generally run substantially slower than non-debug
        builds due to compiler optimizations being disabled and extra
        checks being run.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_App__interface_type"><strong>interface_type</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">str</span></p>
<p style="padding-left: 60px;">Interface mode the game is in; can be 'large', 'medium', or 'small'.</p>

<p style="padding-left: 60px;">        'large' is used by system such as desktop PC where elements on screen
          remain usable even at small sizes, allowing more to be shown.
        'small' is used by small devices such as phones, where elements on
          screen must be larger to remain readable and usable.
        'medium' is used by tablets and other middle-of-the-road situations
          such as VR or TV.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_App__language"><strong>language</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">str</span></p>
<p style="padding-left: 60px;">The name of the language the game is running in.</p>

<p style="padding-left: 60px;">        This can be selected explicitly by the user or may be set
        automatically based on <a href="#attr_ba_App__locale">ba.App.locale</a> or other factors.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_App__locale"><strong>locale</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">str</span></p>
<p style="padding-left: 60px;">Raw country/language code detected by the game (such as 'en_US').</p>

<p style="padding-left: 60px;">        Generally for language-specific code you should look at
        <a href="#attr_ba_App__language">ba.App.language</a>, which is the language the game is using
        (which may differ from locale if the user sets a language, etc.)</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_App__on_tv"><strong>on_tv</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">bool</span></p>
<p style="padding-left: 60px;">Bool value for if the game is running on a TV.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_App__platform"><strong>platform</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">str</span></p>
<p style="padding-left: 60px;">Name of the current platform.</p>

<p style="padding-left: 60px;">        Examples are: 'mac', 'windows', android'.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_App__subplatform"><strong>subplatform</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">str</span></p>
<p style="padding-left: 60px;">String for subplatform.</p>

<p style="padding-left: 60px;">        Can be empty. For the 'android' platform, subplatform may
        be 'google', 'amazon', etc.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_App__system_scripts_directory"><strong>system_scripts_directory</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">str</span></p>
<p style="padding-left: 60px;">Path where the game is looking for its bundled scripts.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_App__test_build"><strong>test_build</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">bool</span></p>
<p style="padding-left: 60px;">Whether the game was compiled in test mode.</p>

<p style="padding-left: 60px;">        Test mode enables extra checks and features that are useful for
        release testing but which do not slow the game down significantly.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_App__ui_bounds"><strong>ui_bounds</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">Tuple[float, float, float, float]</span></p>
<p style="padding-left: 60px;">Bounds of the 'safe' screen area in ui space.</p>

<p style="padding-left: 60px;">        This tuple contains: (x-min, x-max, y-min, y-max)</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_App__user_agent_string"><strong>user_agent_string</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">str</span></p>
<p style="padding-left: 60px;">String containing various bits of info about OS/device/etc.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_App__user_scripts_directory"><strong>user_scripts_directory</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">str</span></p>
<p style="padding-left: 60px;">Path where the game is looking for custom user scripts.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_App__version"><strong>version</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">str</span></p>
<p style="padding-left: 60px;">Human-readable version string; something like '1.3.24'.</p>

<p style="padding-left: 60px;">        This should not be interpreted as a number; it may contain
        string elements such as 'alpha', 'beta', 'test', etc.
        If a numeric version is needed, use '<a href="#attr_ba_App__build_number">ba.App.build_number</a>'.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_App__vr_mode"><strong>vr_mode</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">bool</span></p>
<p style="padding-left: 60px;">Bool value for if the game is running in VR.</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_App__handle_app_pause">handle_app_pause()</a>, <a href="#method_ba_App__handle_app_resume">handle_app_resume()</a>, <a href="#method_ba_App__handle_deep_link">handle_deep_link()</a>, <a href="#method_ba_App__launch_coop_game">launch_coop_game()</a>, <a href="#method_ba_App__pause">pause()</a>, <a href="#method_ba_App__resume">resume()</a>, <a href="#method_ba_App__return_to_main_menu_session_gracefully">return_to_main_menu_session_gracefully()</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_App__handle_app_pause"><strong>handle_app_pause()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">handle_app_pause(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Called when the app goes to a suspended state.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_App__handle_app_resume"><strong>handle_app_resume()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">handle_app_resume(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Run when the app resumes from a suspended state.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_App__handle_deep_link"><strong>handle_deep_link()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">handle_deep_link(self, url: str) -&gt; None</span></p>

<p style="padding-left: 60px;">Handle a deep link URL.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_App__launch_coop_game"><strong>launch_coop_game()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">launch_coop_game(self, game: str, force: bool = False, args: Dict = None) -&gt; bool</span></p>

<p style="padding-left: 60px;">High level way to launch a co-op session locally.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_App__pause"><strong>pause()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">pause(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Pause the game due to a user request or menu popping up.</p>

<p style="padding-left: 60px;">If there's a foreground host-activity that says it's pausable, tell it
to pause ..we now no longer pause if there are connected clients.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_App__resume"><strong>resume()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">resume(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Resume the game due to a user request or menu closing.</p>

<p style="padding-left: 60px;">If there's a foreground host-activity that's currently paused, tell it
to resume.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_App__return_to_main_menu_session_gracefully"><strong>return_to_main_menu_session_gracefully()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">return_to_main_menu_session_gracefully(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Attempt to cleanly get back to the main menu.</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_AppConfig">ba.AppConfig</a></strong></h3>
<p style="padding-left: 30px;">inherits from: dict</p>
<p style="padding-left: 30px;">A special dict that holds the game's persistent configuration values.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_General_Utility_Classes">General Utility Classes</a></p>

<p style="padding-left: 30px;">    It also provides methods for fetching values with app-defined fallback
    defaults, applying contained values to the game, and committing the
    config to storage.</p>

<p style="padding-left: 30px;">    Call ba.appconfig() to get the single shared instance of this class.</p>

<p style="padding-left: 30px;">    AppConfig data is stored as json on disk on so make sure to only place
    json-friendly values in it (dict, list, str, float, int, bool).
    Be aware that tuples will be quietly converted to lists.
</p>

<h3 style="padding-left: 0px;">Methods Defined or Overridden:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_AppConfig__apply">apply()</a>, <a href="#method_ba_AppConfig__apply_and_commit">apply_and_commit()</a>, <a href="#method_ba_AppConfig__builtin_keys">builtin_keys()</a>, <a href="#method_ba_AppConfig__commit">commit()</a>, <a href="#method_ba_AppConfig__default_value">default_value()</a>, <a href="#method_ba_AppConfig__resolve">resolve()</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_AppConfig__apply"><strong>apply()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">apply(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Apply config values to the running app.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_AppConfig__apply_and_commit"><strong>apply_and_commit()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">apply_and_commit(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Run apply() followed by commit(); for convenience.</p>

<p style="padding-left: 60px;">(This way the commit() will not occur if apply() hits invalid data)</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_AppConfig__builtin_keys"><strong>builtin_keys()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">builtin_keys(self) -&gt; List[str]</span></p>

<p style="padding-left: 60px;">Return the list of valid key names recognized by <a href="#class_ba_AppConfig">ba.AppConfig</a>.</p>

<p style="padding-left: 60px;">This set of keys can be used with resolve(), default_value(), etc.
It does not vary across platforms and may include keys that are
obsolete or not relevant on the current running version. (for instance,
VR related keys on non-VR platforms). This is to minimize the amount
of platform checking necessary)</p>

<p style="padding-left: 60px;">Note that it is perfectly legal to store arbitrary named data in the
config, but in that case it is up to the user to test for the existence
of the key in the config dict, fall back to consistent defaults, etc.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_AppConfig__commit"><strong>commit()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">commit(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Commits the config to local storage.</p>

<p style="padding-left: 60px;">Note that this call is asynchronous so the actual write to disk may not
occur immediately.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_AppConfig__default_value"><strong>default_value()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">default_value(self, key: str) -&gt; Any</span></p>

<p style="padding-left: 60px;">Given a string key, return its predefined default value.</p>

<p style="padding-left: 60px;">This is the value that will be returned by <a href="#method_ba_AppConfig__resolve">ba.AppConfig.resolve</a>() if
the key is not present in the config dict or of an incompatible type.</p>

<p style="padding-left: 60px;">Raises an Exception for unrecognized key names. To get the list of keys
supported by this method, use <a href="#method_ba_AppConfig__builtin_keys">ba.AppConfig.builtin_keys</a>(). Note that it
is perfectly legal to store other data in the config; it just needs to
be accessed through standard dict methods and missing values handled
manually.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_AppConfig__resolve"><strong>resolve()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">resolve(self, key: str) -&gt; Any</span></p>

<p style="padding-left: 60px;">Given a string key, return a config value (type varies).</p>

<p style="padding-left: 60px;">This will substitute application defaults for values not present in
the config dict, filter some invalid values, etc.  Note that these
values do not represent the state of the app; simply the state of its
config. Use <a href="#class_ba_App">ba.App</a> to access actual live state.</p>

<p style="padding-left: 60px;">Raises an Exception for unrecognized key names. To get the list of keys
supported by this method, use <a href="#method_ba_AppConfig__builtin_keys">ba.AppConfig.builtin_keys</a>(). Note that it
is perfectly legal to store other data in the config; it just needs to
be accessed through standard dict methods and missing values handled
manually.</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_AppDelegate">ba.AppDelegate</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">Defines handlers for high level app functionality.</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_AppDelegate__create_default_game_config_ui"><strong>create_default_game_config_ui()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">create_default_game_config_ui(self, gameclass: Type[<a href="#class_ba_GameActivity">ba.GameActivity</a>], sessionclass: Type[<a href="#class_ba_Session">ba.Session</a>], config: Optional[Dict[str, Any]], completion_call: Callable[[Optional[Dict[str, Any]]], None]) -&gt; None</span></p>

<p style="padding-left: 60px;">Launch a UI to configure the given game config.</p>

<p style="padding-left: 60px;">It should manipulate the contents of config and call completion_call
when done.</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_AssetPackage">ba.AssetPackage</a></strong></h3>
<p style="padding-left: 30px;">inherits from: <a href="#class_ba_DependencyComponent">ba.DependencyComponent</a></p>
<p style="padding-left: 30px;">DependencyComponent representing a bundled package of game assets.</p>

<h3 style="padding-left: 0px;">Methods Inherited:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_DependencyComponent__get_dynamic_deps">get_dynamic_deps()</a></h5>
<h3 style="padding-left: 0px;">Methods Defined or Overridden:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_AssetPackage____init__">&lt;constructor&gt;</a>, <a href="#method_ba_AssetPackage__dep_is_present">dep_is_present()</a>, <a href="#method_ba_AssetPackage__getcollidemodel">getcollidemodel()</a>, <a href="#method_ba_AssetPackage__getdata">getdata()</a>, <a href="#method_ba_AssetPackage__getmodel">getmodel()</a>, <a href="#method_ba_AssetPackage__getsound">getsound()</a>, <a href="#method_ba_AssetPackage__gettexture">gettexture()</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_AssetPackage____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.AssetPackage()</span></p>

<p style="padding-left: 60px;">Instantiate a DependencyComponent.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_AssetPackage__dep_is_present"><strong>dep_is_present()</strong></a></h4>
<h5 style="padding-left: 60px;"><span style="color: #CC6600;"><em>&lt;class method&gt;</span></em></h5>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">dep_is_present(config: Any = None) -&gt; bool </span></p>

<p style="padding-left: 60px;">Return whether this component/config is present on this device.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_AssetPackage__getcollidemodel"><strong>getcollidemodel()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">getcollidemodel(self, name: str) -&gt; <a href="#class_ba_CollideModel">ba.CollideModel</a></span></p>

<p style="padding-left: 60px;">Load a named <a href="#class_ba_CollideModel">ba.CollideModel</a> from the AssetPackage.</p>

<p style="padding-left: 60px;">Behavior is similar to ba.getcollideModel()</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_AssetPackage__getdata"><strong>getdata()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">getdata(self, name: str) -&gt; <a href="#class_ba_Data">ba.Data</a></span></p>

<p style="padding-left: 60px;">Load a named <a href="#class_ba_Data">ba.Data</a> from the AssetPackage.</p>

<p style="padding-left: 60px;">Behavior is similar to ba.getdata()</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_AssetPackage__getmodel"><strong>getmodel()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">getmodel(self, name: str) -&gt; <a href="#class_ba_Model">ba.Model</a></span></p>

<p style="padding-left: 60px;">Load a named <a href="#class_ba_Model">ba.Model</a> from the AssetPackage.</p>

<p style="padding-left: 60px;">Behavior is similar to <a href="#function_ba_getmodel">ba.getmodel</a>()</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_AssetPackage__getsound"><strong>getsound()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">getsound(self, name: str) -&gt; <a href="#class_ba_Sound">ba.Sound</a></span></p>

<p style="padding-left: 60px;">Load a named <a href="#class_ba_Sound">ba.Sound</a> from the AssetPackage.</p>

<p style="padding-left: 60px;">Behavior is similar to <a href="#function_ba_getsound">ba.getsound</a>()</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_AssetPackage__gettexture"><strong>gettexture()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">gettexture(self, name: str) -&gt; <a href="#class_ba_Texture">ba.Texture</a></span></p>

<p style="padding-left: 60px;">Load a named <a href="#class_ba_Texture">ba.Texture</a> from the AssetPackage.</p>

<p style="padding-left: 60px;">Behavior is similar to <a href="#function_ba_gettexture">ba.gettexture</a>()</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_Call">ba.Call</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">Wraps a callable and arguments into a single callable object.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_General_Utility_Classes">General Utility Classes</a></p>

<p style="padding-left: 30px;">    The callable is strong-referenced so it won't die until this
    object does.</p>

<p style="padding-left: 30px;">    Note that a bound method (ex: myobj.dosomething) contains a reference
    to 'self' (myobj in that case), so you will be keeping that object
    alive too. Use <a href="#class_ba_WeakCall">ba.WeakCall</a> if you want to pass a method to callback
    without keeping its object alive.
</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Call____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.Call(*args: Any, **keywds: Any)</span></p>

<p style="padding-left: 60px;">Instantiate a Call; pass a callable as the first
arg, followed by any number of arguments or keywords.</p>

<pre style="padding-left: 60px;"><span style="color: #008800;"># Example: wrap a method call with 1 positional and 1 keyword arg.</span>
mycall = ba.Call(myobj.dostuff, argval1, namedarg=argval2)</pre>

<pre style="padding-left: 60px;"><span style="color: #008800;"># Now we have a single callable to run that whole mess.</span>
<span style="color: #008800;"># ..the same as calling myobj.dostuff(argval1, namedarg=argval2)</span>
mycall()</pre>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_Campaign">ba.Campaign</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">Represents a unique set or series of <a href="#class_ba_Level">ba.Levels</a>.</p>

<h3 style="padding-left: 0px;">Attributes:</h3>
<h5 style="padding-left: 30px;"><a href="#attr_ba_Campaign__name">name</a>, <a href="#attr_ba_Campaign__sequential">sequential</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Campaign__name"><strong>name</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">str</span></p>
<p style="padding-left: 60px;">The name of the Campaign.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Campaign__sequential"><strong>sequential</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">bool</span></p>
<p style="padding-left: 60px;">Whether this Campaign's levels must be played in sequence.</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_Campaign____init__">&lt;constructor&gt;</a>, <a href="#method_ba_Campaign__add_level">add_level()</a>, <a href="#method_ba_Campaign__get_config_dict">get_config_dict()</a>, <a href="#method_ba_Campaign__get_level">get_level()</a>, <a href="#method_ba_Campaign__get_levels">get_levels()</a>, <a href="#method_ba_Campaign__get_selected_level">get_selected_level()</a>, <a href="#method_ba_Campaign__reset">reset()</a>, <a href="#method_ba_Campaign__set_selected_level">set_selected_level()</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Campaign____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.Campaign(name: str, sequential: bool = True)</span></p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Campaign__add_level"><strong>add_level()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">add_level(self, level: <a href="#class_ba_Level">ba.Level</a>) -&gt; None</span></p>

<p style="padding-left: 60px;">Adds a <a href="#class_ba_Level">ba.Level</a> to the Campaign.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Campaign__get_config_dict"><strong>get_config_dict()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_config_dict(self) -&gt; Dict[str, Any]</span></p>

<p style="padding-left: 60px;">Return the live config dict for this campaign.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Campaign__get_level"><strong>get_level()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_level(self, name: str) -&gt; <a href="#class_ba_Level">ba.Level</a></span></p>

<p style="padding-left: 60px;">Return a contained <a href="#class_ba_Level">ba.Level</a> by name.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Campaign__get_levels"><strong>get_levels()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_levels(self) -&gt; List[<a href="#class_ba_Level">ba.Level</a>]</span></p>

<p style="padding-left: 60px;">Return the set of <a href="#class_ba_Level">ba.Levels</a> in the Campaign.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Campaign__get_selected_level"><strong>get_selected_level()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_selected_level(self) -&gt; str</span></p>

<p style="padding-left: 60px;">Return the name of the Level currently selected in the UI.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Campaign__reset"><strong>reset()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">reset(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Reset state for the Campaign.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Campaign__set_selected_level"><strong>set_selected_level()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">set_selected_level(self, levelname: str) -&gt; None</span></p>

<p style="padding-left: 60px;">Set the Level currently selected in the UI (by name).</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_Chooser">ba.Chooser</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">A character/team selector for a single player.</p>

<h3 style="padding-left: 0px;">Attributes:</h3>
<h5 style="padding-left: 30px;"><a href="#attr_ba_Chooser__lobby">lobby</a>, <a href="#attr_ba_Chooser__player">player</a>, <a href="#attr_ba_Chooser__ready">ready</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Chooser__lobby"><strong>lobby</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"><a href="#class_ba_Lobby">ba.Lobby</a></span></p>
<p style="padding-left: 60px;">The chooser's <a href="#class_ba_Lobby">ba.Lobby</a>.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Chooser__player"><strong>player</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"><a href="#class_ba_Player">ba.Player</a></span></p>
<p style="padding-left: 60px;">The <a href="#class_ba_Player">ba.Player</a> associated with this chooser.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Chooser__ready"><strong>ready</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">bool</span></p>
<p style="padding-left: 60px;">Whether this chooser is checked in as ready.</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_Chooser____init__">&lt;constructor&gt;</a>, <a href="#method_ba_Chooser__get_character_name">get_character_name()</a>, <a href="#method_ba_Chooser__get_color">get_color()</a>, <a href="#method_ba_Chooser__get_highlight">get_highlight()</a>, <a href="#method_ba_Chooser__get_lobby">get_lobby()</a>, <a href="#method_ba_Chooser__get_team">get_team()</a>, <a href="#method_ba_Chooser__getplayer">getplayer()</a>, <a href="#method_ba_Chooser__handlemessage">handlemessage()</a>, <a href="#method_ba_Chooser__reload_profiles">reload_profiles()</a>, <a href="#method_ba_Chooser__update_from_player_profiles">update_from_player_profiles()</a>, <a href="#method_ba_Chooser__update_position">update_position()</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Chooser____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.Chooser(vpos: float, player: _<a href="#class_ba_Player">ba.Player</a>, lobby: "Lobby")</span></p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Chooser__get_character_name"><strong>get_character_name()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_character_name(self) -&gt; str</span></p>

<p style="padding-left: 60px;">Return the selected character name.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Chooser__get_color"><strong>get_color()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_color(self) -&gt; Sequence[float]</span></p>

<p style="padding-left: 60px;">Return the currently selected color.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Chooser__get_highlight"><strong>get_highlight()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_highlight(self) -&gt; Sequence[float]</span></p>

<p style="padding-left: 60px;">Return the currently selected highlight.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Chooser__get_lobby"><strong>get_lobby()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_lobby(self) -&gt; Optional[<a href="#class_ba_Lobby">ba.Lobby</a>]</span></p>

<p style="padding-left: 60px;">Return this chooser's lobby if it still exists; otherwise None.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Chooser__get_team"><strong>get_team()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_team(self) -&gt; <a href="#class_ba_Team">ba.Team</a></span></p>

<p style="padding-left: 60px;">Return this chooser's selected <a href="#class_ba_Team">ba.Team</a>.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Chooser__getplayer"><strong>getplayer()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">getplayer(self) -&gt; <a href="#class_ba_Player">ba.Player</a></span></p>

<p style="padding-left: 60px;">Return the player associated with this chooser.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Chooser__handlemessage"><strong>handlemessage()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">handlemessage(self, msg: Any) -&gt; Any</span></p>

<p style="padding-left: 60px;">Standard generic message handler.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Chooser__reload_profiles"><strong>reload_profiles()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">reload_profiles(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Reload all player profiles.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Chooser__update_from_player_profiles"><strong>update_from_player_profiles()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">update_from_player_profiles(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Set character based on profile; otherwise use pre-picked random.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Chooser__update_position"><strong>update_position()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">update_position(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Update this chooser's position.</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_CollideModel">ba.CollideModel</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">A reference to a collide-model.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Asset_Classes">Asset Classes</a></p>

<p style="padding-left: 30px;">Use <a href="#function_ba_getcollidemodel">ba.getcollidemodel</a>() to instantiate one.</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_Context">ba.Context</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">Context(source: Any)</p>

<p style="padding-left: 30px;">A game context state.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_General_Utility_Classes">General Utility Classes</a></p>

<p style="padding-left: 30px;">Many operations such as <a href="#function_ba_newnode">ba.newnode</a>() or <a href="#function_ba_gettexture">ba.gettexture</a>() operate
implicitly on the current context. Each <a href="#class_ba_Activity">ba.Activity</a> has its own
Context and objects within that activity (nodes, media, etc) can only
interact with other objects from that context.</p>

<p style="padding-left: 30px;">In general, as a modder, you should not need to worry about contexts,
since timers and other callbacks will take care of saving and
restoring the context automatically, but there may be rare cases where
you need to deal with them, such as when loading media in for use in
the UI (there is a special 'ui' context for all user-interface-related
functionality)</p>

<p style="padding-left: 30px;">When instantiating a <a href="#class_ba_Context">ba.Context</a> instance, a single 'source' argument
is passed, which can be one of the following strings/objects:</p>

<p style="padding-left: 30px;">'empty':
  Gives an empty context; it can be handy to run code here to ensure
  it does no loading of media, creation of nodes, etc.</p>

<p style="padding-left: 30px;">'current':
  Sets the context object to the current context.</p>

<p style="padding-left: 30px;">'ui':
  Sets to the UI context. UI functions as well as loading of media to
  be used in said functions must happen in the UI context.</p>

<p style="padding-left: 30px;">a <a href="#class_ba_Activity">ba.Activity</a> instance:
  Gives the context for the provided <a href="#class_ba_Activity">ba.Activity</a>.
  Most all code run during a game happens in an Activity's Context.</p>

<p style="padding-left: 30px;">a <a href="#class_ba_Session">ba.Session</a> instance:
  Gives the context for the provided <a href="#class_ba_Session">ba.Session</a>.
  Generally a user should not need to run anything here.</p>

<p style="padding-left: 30px;"><strong>
Usage:</strong></p>

<p style="padding-left: 30px;">Contexts are generally used with the python 'with' statement, which
sets the context as current on entry and resets it to the previous
value on exit.</p>

<pre style="padding-left: 30px;"><span style="color: #008800;"># example: load a few textures into the UI context</span>
<span style="color: #008800;"># (for use in widgets, etc)</span>
with <a href="#class_ba_Context">ba.Context</a>('ui'):
   tex1 = <a href="#function_ba_gettexture">ba.gettexture</a>('foo_tex_1')
   tex2 = <a href="#function_ba_gettexture">ba.gettexture</a>('foo_tex_2')</pre>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_ContextCall">ba.ContextCall</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">ContextCall(call: Callable)</p>

<p style="padding-left: 30px;">A context-preserving callable.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_General_Utility_Classes">General Utility Classes</a></p>

<p style="padding-left: 30px;">A ContextCall wraps a callable object along with a reference
to the current context (see <a href="#class_ba_Context">ba.Context</a>); it handles restoring the
context when run and automatically clears itself if the context
it belongs to shuts down.</p>

<p style="padding-left: 30px;">Generally you should not need to use this directly; all standard
Ballistica callbacks involved with timers, materials, UI functions,
etc. handle this under-the-hood you don't have to worry about it.
The only time it may be necessary is if you are implementing your
own callbacks, such as a worker thread that does some action and then
runs some game code when done. By wrapping said callback in one of
these, you can ensure that you will not inadvertently be keeping the
current activity alive or running code in a torn-down (expired)
context.</p>

<p style="padding-left: 30px;">You can also use <a href="#class_ba_WeakCall">ba.WeakCall</a> for similar functionality, but
ContextCall has the added bonus that it will not run during context
shutdown, whereas <a href="#class_ba_WeakCall">ba.WeakCall</a> simply looks at whether the target
object still exists.</p>

<pre style="padding-left: 30px;"><span style="color: #008800;"># example A: code like this can inadvertently prevent our activity</span>
<span style="color: #008800;"># (self) from ending until the operation completes, since the bound</span>
<span style="color: #008800;"># method we're passing (self.dosomething) contains a strong-reference</span>
<span style="color: #008800;"># to self).</span>
start_some_long_action(callback_when_done=self.dosomething)</pre>

<pre style="padding-left: 30px;"><span style="color: #008800;"># example B: in this case our activity (self) can still die</span>
<span style="color: #008800;"># properly; the callback will clear itself when the activity starts</span>
<span style="color: #008800;"># shutting down, becoming a harmless no-op and releasing the reference</span>
<span style="color: #008800;"># to our activity.</span>
start_long_action(callback_when_done=<a href="#class_ba_ContextCall">ba.ContextCall</a>(self.mycallback))</pre>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_CoopGameActivity">ba.CoopGameActivity</a></strong></h3>
<p style="padding-left: 30px;">inherits from: <a href="#class_ba_GameActivity">ba.GameActivity</a>, <a href="#class_ba_Activity">ba.Activity</a>, <a href="#class_ba_DependencyComponent">ba.DependencyComponent</a></p>
<p style="padding-left: 30px;">Base class for cooperative-mode games.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a>
</p>

<h3 style="padding-left: 0px;">Attributes Inherited:</h3>
<h5 style="padding-left: 30px;"><a href="#attr_ba_Activity__players">players</a>, <a href="#attr_ba_Activity__settings">settings</a>, <a href="#attr_ba_Activity__teams">teams</a></h5>
<h3 style="padding-left: 0px;">Attributes Defined Here:</h3>
<h5 style="padding-left: 30px;"><a href="#attr_ba_CoopGameActivity__map">map</a>, <a href="#attr_ba_CoopGameActivity__session">session</a>, <a href="#attr_ba_CoopGameActivity__stats">stats</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_CoopGameActivity__map"><strong>map</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"><a href="#class_ba_Map">ba.Map</a></span></p>
<p style="padding-left: 60px;">The map being used for this game.</p>

<p style="padding-left: 60px;">        Raises a <a href="#class_ba_NotFoundError">ba.NotFoundError</a> if the map does not currently exist.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_CoopGameActivity__session"><strong>session</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"><a href="#class_ba_Session">ba.Session</a></span></p>
<p style="padding-left: 60px;">The <a href="#class_ba_Session">ba.Session</a> this <a href="#class_ba_Activity">ba.Activity</a> belongs go.</p>

<p style="padding-left: 60px;">        Raises a <a href="#class_ba_SessionNotFoundError">ba.SessionNotFoundError</a> if the Session no longer exists.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_CoopGameActivity__stats"><strong>stats</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"><a href="#class_ba_Stats">ba.Stats</a></span></p>
<p style="padding-left: 60px;">The stats instance accessible while the activity is running.</p>

<p style="padding-left: 60px;">        If access is attempted before or after, raises a <a href="#class_ba_NotFoundError">ba.NotFoundError</a>.</p>

<h3 style="padding-left: 0px;">Methods Inherited:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_GameActivity__add_actor_weak_ref">add_actor_weak_ref()</a>, <a href="#method_ba_GameActivity__begin">begin()</a>, <a href="#method_ba_GameActivity__continue_or_end_game">continue_or_end_game()</a>, <a href="#method_ba_GameActivity__create_config_ui">create_config_ui()</a>, <a href="#method_ba_GameActivity__create_player_node">create_player_node()</a>, <a href="#method_ba_GameActivity__dep_is_present">dep_is_present()</a>, <a href="#method_ba_GameActivity__end">end()</a>, <a href="#method_ba_GameActivity__end_game">end_game()</a>, <a href="#method_ba_GameActivity__get_config_display_string">get_config_display_string()</a>, <a href="#method_ba_GameActivity__get_description">get_description()</a>, <a href="#method_ba_GameActivity__get_description_display_string">get_description_display_string()</a>, <a href="#method_ba_GameActivity__get_display_string">get_display_string()</a>, <a href="#method_ba_GameActivity__get_dynamic_deps">get_dynamic_deps()</a>, <a href="#method_ba_GameActivity__get_instance_description">get_instance_description()</a>, <a href="#method_ba_GameActivity__get_instance_display_string">get_instance_display_string()</a>, <a href="#method_ba_GameActivity__get_instance_scoreboard_description">get_instance_scoreboard_description()</a>, <a href="#method_ba_GameActivity__get_instance_scoreboard_display_string">get_instance_scoreboard_display_string()</a>, <a href="#method_ba_GameActivity__get_name">get_name()</a>, <a href="#method_ba_GameActivity__get_resolved_score_info">get_resolved_score_info()</a>, <a href="#method_ba_GameActivity__get_score_info">get_score_info()</a>, <a href="#method_ba_GameActivity__get_settings">get_settings()</a>, <a href="#method_ba_GameActivity__get_supported_maps">get_supported_maps()</a>, <a href="#method_ba_GameActivity__get_team_display_string">get_team_display_string()</a>, <a href="#method_ba_GameActivity__handlemessage">handlemessage()</a>, <a href="#method_ba_GameActivity__has_begun">has_begun()</a>, <a href="#method_ba_GameActivity__has_ended">has_ended()</a>, <a href="#method_ba_GameActivity__has_transitioned_in">has_transitioned_in()</a>, <a href="#method_ba_GameActivity__is_expired">is_expired()</a>, <a href="#method_ba_GameActivity__is_transitioning_out">is_transitioning_out()</a>, <a href="#method_ba_GameActivity__is_waiting_for_continue">is_waiting_for_continue()</a>, <a href="#method_ba_GameActivity__on_continue">on_continue()</a>, <a href="#method_ba_GameActivity__on_expire">on_expire()</a>, <a href="#method_ba_GameActivity__on_player_join">on_player_join()</a>, <a href="#method_ba_GameActivity__on_player_leave">on_player_leave()</a>, <a href="#method_ba_GameActivity__on_team_join">on_team_join()</a>, <a href="#method_ba_GameActivity__on_team_leave">on_team_leave()</a>, <a href="#method_ba_GameActivity__on_transition_in">on_transition_in()</a>, <a href="#method_ba_GameActivity__on_transition_out">on_transition_out()</a>, <a href="#method_ba_GameActivity__project_flag_stand">project_flag_stand()</a>, <a href="#method_ba_GameActivity__respawn_player">respawn_player()</a>, <a href="#method_ba_GameActivity__retain_actor">retain_actor()</a>, <a href="#method_ba_GameActivity__set_has_ended">set_has_ended()</a>, <a href="#method_ba_GameActivity__set_immediate_end">set_immediate_end()</a>, <a href="#method_ba_GameActivity__setup_standard_powerup_drops">setup_standard_powerup_drops()</a>, <a href="#method_ba_GameActivity__setup_standard_time_limit">setup_standard_time_limit()</a>, <a href="#method_ba_GameActivity__show_info">show_info()</a>, <a href="#method_ba_GameActivity__show_scoreboard_info">show_scoreboard_info()</a>, <a href="#method_ba_GameActivity__show_zoom_message">show_zoom_message()</a>, <a href="#method_ba_GameActivity__spawn_player">spawn_player()</a>, <a href="#method_ba_GameActivity__spawn_player_if_exists">spawn_player_if_exists()</a>, <a href="#method_ba_GameActivity__start_transition_in">start_transition_in()</a></h5>
<h3 style="padding-left: 0px;">Methods Defined or Overridden:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_CoopGameActivity____init__">&lt;constructor&gt;</a>, <a href="#method_ba_CoopGameActivity__celebrate">celebrate()</a>, <a href="#method_ba_CoopGameActivity__fade_to_red">fade_to_red()</a>, <a href="#method_ba_CoopGameActivity__get_score_type">get_score_type()</a>, <a href="#method_ba_CoopGameActivity__on_begin">on_begin()</a>, <a href="#method_ba_CoopGameActivity__setup_low_life_warning_sound">setup_low_life_warning_sound()</a>, <a href="#method_ba_CoopGameActivity__spawn_player_spaz">spawn_player_spaz()</a>, <a href="#method_ba_CoopGameActivity__supports_session_type">supports_session_type()</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_CoopGameActivity____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.CoopGameActivity(settings: Dict[str, Any])</span></p>

<p style="padding-left: 60px;">Instantiate the Activity.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_CoopGameActivity__celebrate"><strong>celebrate()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">celebrate(self, duration: float) -&gt; None</span></p>

<p style="padding-left: 60px;">Tells all existing player-controlled characters to celebrate.</p>

<p style="padding-left: 60px;">Can be useful in co-op games when the good guys score or complete
a wave.
duration is given in seconds.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_CoopGameActivity__fade_to_red"><strong>fade_to_red()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">fade_to_red(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Fade the screen to red; (such as when the good guys have lost).</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_CoopGameActivity__get_score_type"><strong>get_score_type()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_score_type(self) -&gt; str</span></p>

<p style="padding-left: 60px;">Return the score unit this co-op game uses ('point', 'seconds', etc.)</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_CoopGameActivity__on_begin"><strong>on_begin()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">on_begin(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Called once the previous <a href="#class_ba_Activity">ba.Activity</a> has finished transitioning out.</p>

<p style="padding-left: 60px;">At this point the activity's initial players and teams are filled in
and it should begin its actual game logic.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_CoopGameActivity__setup_low_life_warning_sound"><strong>setup_low_life_warning_sound()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">setup_low_life_warning_sound(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Set up a beeping noise to play when any players are near death.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_CoopGameActivity__spawn_player_spaz"><strong>spawn_player_spaz()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">spawn_player_spaz(self, player: <a href="#class_ba_Player">ba.Player</a>, position: Sequence[float] = (0.0, 0.0, 0.0), angle: float = None) -&gt; PlayerSpaz</span></p>

<p style="padding-left: 60px;">Spawn and wire up a standard player spaz.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_CoopGameActivity__supports_session_type"><strong>supports_session_type()</strong></a></h4>
<h5 style="padding-left: 60px;"><span style="color: #CC6600;"><em>&lt;class method&gt;</span></em></h5>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">supports_session_type(sessiontype: Type[<a href="#class_ba_Session">ba.Session</a>]) -&gt; bool </span></p>

<p style="padding-left: 60px;">Return whether this game supports the provided Session type.</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_CoopSession">ba.CoopSession</a></strong></h3>
<p style="padding-left: 30px;">inherits from: <a href="#class_ba_Session">ba.Session</a></p>
<p style="padding-left: 30px;">A <a href="#class_ba_Session">ba.Session</a> which runs cooperative-mode games.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a></p>

<p style="padding-left: 30px;">    These generally consist of 1-4 players against
    the computer and include functionality such as
    high score lists.
</p>

<h3 style="padding-left: 0px;">Attributes Inherited:</h3>
<h5 style="padding-left: 30px;"><a href="#attr_ba_Session__campaign">campaign</a>, <a href="#attr_ba_Session__lobby">lobby</a>, <a href="#attr_ba_Session__max_players">max_players</a>, <a href="#attr_ba_Session__min_players">min_players</a>, <a href="#attr_ba_Session__players">players</a>, <a href="#attr_ba_Session__teams">teams</a></h5>
<h3 style="padding-left: 0px;">Methods Inherited:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_Session__begin_next_activity">begin_next_activity()</a>, <a href="#method_ba_Session__end">end()</a>, <a href="#method_ba_Session__end_activity">end_activity()</a>, <a href="#method_ba_Session__getactivity">getactivity()</a>, <a href="#method_ba_Session__handlemessage">handlemessage()</a>, <a href="#method_ba_Session__launch_end_session_activity">launch_end_session_activity()</a>, <a href="#method_ba_Session__on_player_request">on_player_request()</a>, <a href="#method_ba_Session__on_team_join">on_team_join()</a>, <a href="#method_ba_Session__on_team_leave">on_team_leave()</a>, <a href="#method_ba_Session__set_activity">set_activity()</a></h5>
<h3 style="padding-left: 0px;">Methods Defined or Overridden:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_CoopSession____init__">&lt;constructor&gt;</a>, <a href="#method_ba_CoopSession__get_current_game_instance">get_current_game_instance()</a>, <a href="#method_ba_CoopSession__get_custom_menu_entries">get_custom_menu_entries()</a>, <a href="#method_ba_CoopSession__on_activity_end">on_activity_end()</a>, <a href="#method_ba_CoopSession__on_player_leave">on_player_leave()</a>, <a href="#method_ba_CoopSession__restart">restart()</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_CoopSession____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.CoopSession()</span></p>

<p style="padding-left: 60px;">Instantiate a co-op mode session.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_CoopSession__get_current_game_instance"><strong>get_current_game_instance()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_current_game_instance(self) -&gt; <a href="#class_ba_GameActivity">ba.GameActivity</a></span></p>

<p style="padding-left: 60px;">Get the game instance currently being played.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_CoopSession__get_custom_menu_entries"><strong>get_custom_menu_entries()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_custom_menu_entries(self) -&gt; List[Dict[str, Any]]</span></p>

<p style="padding-left: 60px;">Subclasses can override this to provide custom menu entries.</p>

<p style="padding-left: 60px;">The returned value should be a list of dicts, each containing
a 'label' and 'call' entry, with 'label' being the text for
the entry and 'call' being the callable to trigger if the entry
is pressed.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_CoopSession__on_activity_end"><strong>on_activity_end()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">on_activity_end(self, activity: <a href="#class_ba_Activity">ba.Activity</a>, results: Any) -&gt; None</span></p>

<p style="padding-left: 60px;">Method override for co-op sessions.</p>

<p style="padding-left: 60px;">Jumps between co-op games and score screens.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_CoopSession__on_player_leave"><strong>on_player_leave()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">on_player_leave(self, player: <a href="#class_ba_Player">ba.Player</a>) -&gt; None</span></p>

<p style="padding-left: 60px;">Called when a previously-accepted <a href="#class_ba_Player">ba.Player</a> leaves the session.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_CoopSession__restart"><strong>restart()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">restart(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Restart the current game activity.</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_Data">ba.Data</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">A reference to a data object.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Asset_Classes">Asset Classes</a></p>

<p style="padding-left: 30px;">Use ba.getdata() to instantiate one.</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Data__getvalue"><strong>getvalue()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">getvalue() -&gt; Any</span></p>

<p style="padding-left: 60px;">Return the data object's value.</p>

<p style="padding-left: 60px;">This can consist of anything representable by json (dicts, lists,
numbers, bools, None, etc).
Note that this call will block if the data has not yet been loaded,
so it can be beneficial to plan a short bit of time between when
the data object is requested and when it's value is accessed.</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_Dependency">ba.Dependency</a></strong></h3>
<p style="padding-left: 30px;">inherits from: <a href="#class_typing_Generic">typing.Generic</a></p>
<p style="padding-left: 30px;">A dependency on a DependencyComponent (with an optional config).</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Dependency_Classes">Dependency Classes</a></p>

<p style="padding-left: 30px;">    This class is used to request and access functionality provided
    by other DependencyComponent classes from a DependencyComponent class.
    The class functions as a descriptor, allowing dependencies to
    be added at a class level much the same as properties or methods
    and then used with class instances to access those dependencies.
    For instance, if you do 'floofcls = <a href="#class_ba_Dependency">ba.Dependency</a>(FloofClass)' you
    would then be able to instantiate a FloofClass in your class's
    methods via self.floofcls().
</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_Dependency____init__">&lt;constructor&gt;</a>, <a href="#method_ba_Dependency__get_hash">get_hash()</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Dependency____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.Dependency(cls: Type[T], config: Any = None)</span></p>

<p style="padding-left: 60px;">Instantiate a Dependency given a <a href="#class_ba_DependencyComponent">ba.DependencyComponent</a> type.</p>

<p style="padding-left: 60px;">Optionally, an arbitrary object can be passed as 'config' to
influence dependency calculation for the target class.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Dependency__get_hash"><strong>get_hash()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_hash(self) -&gt; int</span></p>

<p style="padding-left: 60px;">Return the dependency's hash, calculating it if necessary.</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_DependencyComponent">ba.DependencyComponent</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">Base class for all classes that can act as or use dependencies.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Dependency_Classes">Dependency Classes</a>
</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_DependencyComponent____init__">&lt;constructor&gt;</a>, <a href="#method_ba_DependencyComponent__dep_is_present">dep_is_present()</a>, <a href="#method_ba_DependencyComponent__get_dynamic_deps">get_dynamic_deps()</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_DependencyComponent____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.DependencyComponent()</span></p>

<p style="padding-left: 60px;">Instantiate a DependencyComponent.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_DependencyComponent__dep_is_present"><strong>dep_is_present()</strong></a></h4>
<h5 style="padding-left: 60px;"><span style="color: #CC6600;"><em>&lt;class method&gt;</span></em></h5>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">dep_is_present(config: Any = None) -&gt; bool </span></p>

<p style="padding-left: 60px;">Return whether this component/config is present on this device.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_DependencyComponent__get_dynamic_deps"><strong>get_dynamic_deps()</strong></a></h4>
<h5 style="padding-left: 60px;"><span style="color: #CC6600;"><em>&lt;class method&gt;</span></em></h5>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_dynamic_deps(config: Any = None) -&gt; List[Dependency] </span></p>

<p style="padding-left: 60px;">Return any dynamically-calculated deps for this component/config.</p>

<p style="padding-left: 60px;">Deps declared statically as part of the class do not need to be
included here; this is only for additional deps that may vary based
on the dep config value. (for instance a map required by a game type)</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_DependencyError">ba.DependencyError</a></strong></h3>
<p style="padding-left: 30px;">inherits from: Exception, BaseException</p>
<p style="padding-left: 30px;">Exception raised when one or more <a href="#class_ba_Dependency">ba.Dependency</a> items are missing.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Exception_Classes">Exception Classes</a></p>

<p style="padding-left: 30px;">    (this will generally be missing assets).
</p>

<h3 style="padding-left: 0px;">Attributes:</h3>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_DependencyError__deps"><strong>deps</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">List[<a href="#class_ba_Dependency">ba.Dependency</a>]</span></p>
<p style="padding-left: 60px;">The list of missing dependencies causing this error.</p>

<h3 style="padding-left: 0px;">Methods Inherited:</h3>
<h5 style="padding-left: 30px;"><a href="#method_builtins_Exception__with_traceback">with_traceback()</a></h5>
<h3 style="padding-left: 0px;">Methods Defined or Overridden:</h3>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_DependencyError____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.DependencyError(deps: List[<a href="#class_ba_Dependency">ba.Dependency</a>])</span></p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_DependencySet">ba.DependencySet</a></strong></h3>
<p style="padding-left: 30px;">inherits from: <a href="#class_typing_Generic">typing.Generic</a></p>
<p style="padding-left: 30px;">Set of resolved dependencies and their associated data.</p>

<p style="padding-left: 30px;">    To use DependencyComponents, a set must be created, resolved, and then
    loaded. The DependencyComponents are only valid while the set remains
    in existence.
</p>

<h3 style="padding-left: 0px;">Attributes:</h3>
<h5 style="padding-left: 30px;"><a href="#attr_ba_DependencySet__resolved">resolved</a>, <a href="#attr_ba_DependencySet__root">root</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_DependencySet__resolved"><strong>resolved</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">bool</span></p>
<p style="padding-left: 60px;">Whether this set has been successfully resolved.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_DependencySet__root"><strong>root</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">T</span></p>
<p style="padding-left: 60px;">The instantiated root DependencyComponent instance for the set.</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_DependencySet____init__">&lt;constructor&gt;</a>, <a href="#method_ba_DependencySet__get_asset_package_ids">get_asset_package_ids()</a>, <a href="#method_ba_DependencySet__load">load()</a>, <a href="#method_ba_DependencySet__resolve">resolve()</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_DependencySet____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.DependencySet(root_dependency: Dependency[T])</span></p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_DependencySet__get_asset_package_ids"><strong>get_asset_package_ids()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_asset_package_ids(self) -&gt; Set[str]</span></p>

<p style="padding-left: 60px;">Return the set of asset-package-ids required by this dep-set.</p>

<p style="padding-left: 60px;">Must be called on a resolved dep-set.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_DependencySet__load"><strong>load()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">load(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Instantiate all DependencyComponents in the set.</p>

<p style="padding-left: 60px;">Returns a wrapper which can be used to instantiate the root dep.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_DependencySet__resolve"><strong>resolve()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">resolve(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Resolve the complete set of required dependencies for this set.</p>

<p style="padding-left: 60px;">Raises a <a href="#class_ba_DependencyError">ba.DependencyError</a> if dependencies are missing (or other
Exception types on other errors).</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_DieMessage">ba.DieMessage</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">A message telling an object to die.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Message_Classes">Message Classes</a></p>

<p style="padding-left: 30px;">    Most <a href="#class_ba_Actor">ba.Actors</a> respond to this.</p>

<h3 style="padding-left: 0px;">Attributes:</h3>
<h5 style="padding-left: 30px;"><a href="#attr_ba_DieMessage__how">how</a>, <a href="#attr_ba_DieMessage__immediate">immediate</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_DieMessage__how"><strong>how</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">str</span></p>
<p style="padding-left: 60px;">The particular reason for death; 'fall', 'impact', 'leftGame', etc.
This can be examined for scoring or other purposes.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_DieMessage__immediate"><strong>immediate</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">bool</span></p>
<p style="padding-left: 60px;">If this is set to True, the actor should disappear immediately.
This is for 'removing' stuff from the game more so than 'killing'
it. If False, the actor should die a 'normal' death and can take
its time with lingering corpses, sound effects, etc.</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_DieMessage____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.DieMessage(immediate: 'bool' = False, how: 'str' = 'generic')</span></p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_DropMessage">ba.DropMessage</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">Tells an object that it has dropped what it was holding.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Message_Classes">Message Classes</a>
</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_DropMessage____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.DropMessage()</span></p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_DroppedMessage">ba.DroppedMessage</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">Tells an object that it has been dropped.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Message_Classes">Message Classes</a></p>

<h3 style="padding-left: 0px;">Attributes:</h3>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_DroppedMessage__node"><strong>node</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"><a href="#class_ba_Node">ba.Node</a></span></p>
<p style="padding-left: 60px;">The <a href="#class_ba_Node">ba.Node</a> doing the dropping.</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_DroppedMessage____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.DroppedMessage(node: <a href="#class_ba_Node">ba.Node</a>)</span></p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_FreeForAllSession">ba.FreeForAllSession</a></strong></h3>
<p style="padding-left: 30px;">inherits from: <a href="#class_ba_TeamBaseSession">ba.TeamBaseSession</a>, <a href="#class_ba_Session">ba.Session</a></p>
<p style="padding-left: 30px;"><a href="#class_ba_Session">ba.Session</a> type for free-for-all mode games.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a>
</p>

<h3 style="padding-left: 0px;">Attributes Inherited:</h3>
<h5 style="padding-left: 30px;"><a href="#attr_ba_Session__campaign">campaign</a>, <a href="#attr_ba_Session__lobby">lobby</a>, <a href="#attr_ba_Session__max_players">max_players</a>, <a href="#attr_ba_Session__min_players">min_players</a>, <a href="#attr_ba_Session__players">players</a>, <a href="#attr_ba_Session__teams">teams</a></h5>
<h3 style="padding-left: 0px;">Methods Inherited:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_TeamBaseSession__announce_game_results">announce_game_results()</a>, <a href="#method_ba_TeamBaseSession__begin_next_activity">begin_next_activity()</a>, <a href="#method_ba_TeamBaseSession__end">end()</a>, <a href="#method_ba_TeamBaseSession__end_activity">end_activity()</a>, <a href="#method_ba_TeamBaseSession__get_custom_menu_entries">get_custom_menu_entries()</a>, <a href="#method_ba_TeamBaseSession__get_ffa_series_length">get_ffa_series_length()</a>, <a href="#method_ba_TeamBaseSession__get_game_number">get_game_number()</a>, <a href="#method_ba_TeamBaseSession__get_max_players">get_max_players()</a>, <a href="#method_ba_TeamBaseSession__get_next_game_description">get_next_game_description()</a>, <a href="#method_ba_TeamBaseSession__get_series_length">get_series_length()</a>, <a href="#method_ba_TeamBaseSession__getactivity">getactivity()</a>, <a href="#method_ba_TeamBaseSession__handlemessage">handlemessage()</a>, <a href="#method_ba_TeamBaseSession__launch_end_session_activity">launch_end_session_activity()</a>, <a href="#method_ba_TeamBaseSession__on_activity_end">on_activity_end()</a>, <a href="#method_ba_TeamBaseSession__on_player_leave">on_player_leave()</a>, <a href="#method_ba_TeamBaseSession__on_player_request">on_player_request()</a>, <a href="#method_ba_TeamBaseSession__on_team_join">on_team_join()</a>, <a href="#method_ba_TeamBaseSession__on_team_leave">on_team_leave()</a>, <a href="#method_ba_TeamBaseSession__set_activity">set_activity()</a></h5>
<h3 style="padding-left: 0px;">Methods Defined or Overridden:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_FreeForAllSession____init__">&lt;constructor&gt;</a>, <a href="#method_ba_FreeForAllSession__get_ffa_point_awards">get_ffa_point_awards()</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_FreeForAllSession____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.FreeForAllSession()</span></p>

<p style="padding-left: 60px;">Set up playlists and launches a <a href="#class_ba_Activity">ba.Activity</a> to accept joiners.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_FreeForAllSession__get_ffa_point_awards"><strong>get_ffa_point_awards()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_ffa_point_awards(self) -&gt; Dict[int, int]</span></p>

<p style="padding-left: 60px;">Return the number of points awarded for different rankings.</p>

<p style="padding-left: 60px;">This is based on the current number of players.</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_FreezeMessage">ba.FreezeMessage</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">Tells an object to become frozen.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Message_Classes">Message Classes</a></p>

<p style="padding-left: 30px;">    As seen in the effects of an ice ba.Bomb.
</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_FreezeMessage____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.FreezeMessage()</span></p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_GameActivity">ba.GameActivity</a></strong></h3>
<p style="padding-left: 30px;">inherits from: <a href="#class_ba_Activity">ba.Activity</a>, <a href="#class_ba_DependencyComponent">ba.DependencyComponent</a></p>
<p style="padding-left: 30px;">Common base class for all game ba.Activities.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a>
</p>

<h3 style="padding-left: 0px;">Attributes Inherited:</h3>
<h5 style="padding-left: 30px;"><a href="#attr_ba_Activity__players">players</a>, <a href="#attr_ba_Activity__settings">settings</a>, <a href="#attr_ba_Activity__teams">teams</a></h5>
<h3 style="padding-left: 0px;">Attributes Defined Here:</h3>
<h5 style="padding-left: 30px;"><a href="#attr_ba_GameActivity__map">map</a>, <a href="#attr_ba_GameActivity__session">session</a>, <a href="#attr_ba_GameActivity__stats">stats</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_GameActivity__map"><strong>map</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"><a href="#class_ba_Map">ba.Map</a></span></p>
<p style="padding-left: 60px;">The map being used for this game.</p>

<p style="padding-left: 60px;">        Raises a <a href="#class_ba_NotFoundError">ba.NotFoundError</a> if the map does not currently exist.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_GameActivity__session"><strong>session</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"><a href="#class_ba_Session">ba.Session</a></span></p>
<p style="padding-left: 60px;">The <a href="#class_ba_Session">ba.Session</a> this <a href="#class_ba_Activity">ba.Activity</a> belongs go.</p>

<p style="padding-left: 60px;">        Raises a <a href="#class_ba_SessionNotFoundError">ba.SessionNotFoundError</a> if the Session no longer exists.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_GameActivity__stats"><strong>stats</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"><a href="#class_ba_Stats">ba.Stats</a></span></p>
<p style="padding-left: 60px;">The stats instance accessible while the activity is running.</p>

<p style="padding-left: 60px;">        If access is attempted before or after, raises a <a href="#class_ba_NotFoundError">ba.NotFoundError</a>.</p>

<h3 style="padding-left: 0px;">Methods Inherited:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_Activity__add_actor_weak_ref">add_actor_weak_ref()</a>, <a href="#method_ba_Activity__begin">begin()</a>, <a href="#method_ba_Activity__create_player_node">create_player_node()</a>, <a href="#method_ba_Activity__dep_is_present">dep_is_present()</a>, <a href="#method_ba_Activity__get_dynamic_deps">get_dynamic_deps()</a>, <a href="#method_ba_Activity__has_begun">has_begun()</a>, <a href="#method_ba_Activity__has_ended">has_ended()</a>, <a href="#method_ba_Activity__has_transitioned_in">has_transitioned_in()</a>, <a href="#method_ba_Activity__is_expired">is_expired()</a>, <a href="#method_ba_Activity__is_transitioning_out">is_transitioning_out()</a>, <a href="#method_ba_Activity__on_expire">on_expire()</a>, <a href="#method_ba_Activity__on_team_join">on_team_join()</a>, <a href="#method_ba_Activity__on_team_leave">on_team_leave()</a>, <a href="#method_ba_Activity__on_transition_out">on_transition_out()</a>, <a href="#method_ba_Activity__retain_actor">retain_actor()</a>, <a href="#method_ba_Activity__set_has_ended">set_has_ended()</a>, <a href="#method_ba_Activity__set_immediate_end">set_immediate_end()</a>, <a href="#method_ba_Activity__start_transition_in">start_transition_in()</a></h5>
<h3 style="padding-left: 0px;">Methods Defined or Overridden:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_GameActivity____init__">&lt;constructor&gt;</a>, <a href="#method_ba_GameActivity__continue_or_end_game">continue_or_end_game()</a>, <a href="#method_ba_GameActivity__create_config_ui">create_config_ui()</a>, <a href="#method_ba_GameActivity__end">end()</a>, <a href="#method_ba_GameActivity__end_game">end_game()</a>, <a href="#method_ba_GameActivity__get_config_display_string">get_config_display_string()</a>, <a href="#method_ba_GameActivity__get_description">get_description()</a>, <a href="#method_ba_GameActivity__get_description_display_string">get_description_display_string()</a>, <a href="#method_ba_GameActivity__get_display_string">get_display_string()</a>, <a href="#method_ba_GameActivity__get_instance_description">get_instance_description()</a>, <a href="#method_ba_GameActivity__get_instance_display_string">get_instance_display_string()</a>, <a href="#method_ba_GameActivity__get_instance_scoreboard_description">get_instance_scoreboard_description()</a>, <a href="#method_ba_GameActivity__get_instance_scoreboard_display_string">get_instance_scoreboard_display_string()</a>, <a href="#method_ba_GameActivity__get_name">get_name()</a>, <a href="#method_ba_GameActivity__get_resolved_score_info">get_resolved_score_info()</a>, <a href="#method_ba_GameActivity__get_score_info">get_score_info()</a>, <a href="#method_ba_GameActivity__get_settings">get_settings()</a>, <a href="#method_ba_GameActivity__get_supported_maps">get_supported_maps()</a>, <a href="#method_ba_GameActivity__get_team_display_string">get_team_display_string()</a>, <a href="#method_ba_GameActivity__handlemessage">handlemessage()</a>, <a href="#method_ba_GameActivity__is_waiting_for_continue">is_waiting_for_continue()</a>, <a href="#method_ba_GameActivity__on_begin">on_begin()</a>, <a href="#method_ba_GameActivity__on_continue">on_continue()</a>, <a href="#method_ba_GameActivity__on_player_join">on_player_join()</a>, <a href="#method_ba_GameActivity__on_player_leave">on_player_leave()</a>, <a href="#method_ba_GameActivity__on_transition_in">on_transition_in()</a>, <a href="#method_ba_GameActivity__project_flag_stand">project_flag_stand()</a>, <a href="#method_ba_GameActivity__respawn_player">respawn_player()</a>, <a href="#method_ba_GameActivity__setup_standard_powerup_drops">setup_standard_powerup_drops()</a>, <a href="#method_ba_GameActivity__setup_standard_time_limit">setup_standard_time_limit()</a>, <a href="#method_ba_GameActivity__show_info">show_info()</a>, <a href="#method_ba_GameActivity__show_scoreboard_info">show_scoreboard_info()</a>, <a href="#method_ba_GameActivity__show_zoom_message">show_zoom_message()</a>, <a href="#method_ba_GameActivity__spawn_player">spawn_player()</a>, <a href="#method_ba_GameActivity__spawn_player_if_exists">spawn_player_if_exists()</a>, <a href="#method_ba_GameActivity__spawn_player_spaz">spawn_player_spaz()</a>, <a href="#method_ba_GameActivity__supports_session_type">supports_session_type()</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_GameActivity____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.GameActivity(settings: Dict[str, Any])</span></p>

<p style="padding-left: 60px;">Instantiate the Activity.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_GameActivity__continue_or_end_game"><strong>continue_or_end_game()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">continue_or_end_game(self) -&gt; None</span></p>

<p style="padding-left: 60px;">If continues are allowed, prompts the player to purchase a continue
and calls either end_game or continue_game depending on the result</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_GameActivity__create_config_ui"><strong>create_config_ui()</strong></a></h4>
<h5 style="padding-left: 60px;"><span style="color: #CC6600;"><em>&lt;class method&gt;</span></em></h5>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">create_config_ui(sessionclass: Type[<a href="#class_ba_Session">ba.Session</a>], config: Optional[Dict[str, Any]], completion_call: Callable[[Optional[Dict[str, Any]]], None]) -&gt; None </span></p>

<p style="padding-left: 60px;">Launch an in-game UI to configure settings for a game type.</p>

<p style="padding-left: 60px;">'sessionclass' should be the <a href="#class_ba_Session">ba.Session</a> class the game will be used in.</p>

<p style="padding-left: 60px;">'config' should be an existing config dict (specifies 'edit' ui mode)
  or None (specifies 'add' ui mode).</p>

<p style="padding-left: 60px;">'completion_call' will be called with a filled-out config dict on
  success or None on cancel.</p>

<p style="padding-left: 60px;">Generally subclasses don't need to override this; if they override
<a href="#method_ba_GameActivity__get_settings">ba.GameActivity.get_settings</a>() and <a href="#method_ba_GameActivity__get_supported_maps">ba.GameActivity.get_supported_maps</a>()
they can just rely on the default implementation here which calls those
methods.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_GameActivity__end"><strong>end()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">end(self, results: Any = None, delay: float = 0.0, force: bool = False) -&gt; None</span></p>

<p style="padding-left: 60px;">Commences Activity shutdown and delivers results to the <a href="#class_ba_Session">ba.Session</a>.</p>

<p style="padding-left: 60px;">'delay' is the time delay before the Activity actually ends
(in seconds). Further calls to end() will be ignored up until
this time, unless 'force' is True, in which case the new results
will replace the old.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_GameActivity__end_game"><strong>end_game()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">end_game(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Tells the game to wrap itself up and call <a href="#method_ba_Activity__end">ba.Activity.end</a>()
immediately. This method should be overridden by subclasses.</p>

<p style="padding-left: 60px;">A game should always be prepared to end and deliver results, even if
there is no 'winner' yet; this way things like the standard time-limit
(<a href="#method_ba_GameActivity__setup_standard_time_limit">ba.GameActivity.setup_standard_time_limit</a>()) will work with the game.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_GameActivity__get_config_display_string"><strong>get_config_display_string()</strong></a></h4>
<h5 style="padding-left: 60px;"><span style="color: #CC6600;"><em>&lt;class method&gt;</span></em></h5>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_config_display_string(config: Dict[str, Any]) -&gt; <a href="#class_ba_Lstr">ba.Lstr</a> </span></p>

<p style="padding-left: 60px;">Given a game config dict, return a short description for it.</p>

<p style="padding-left: 60px;">This is used when viewing game-lists or showing what game
is up next in a series.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_GameActivity__get_description"><strong>get_description()</strong></a></h4>
<h5 style="padding-left: 60px;"><span style="color: #CC6600;"><em>&lt;class method&gt;</span></em></h5>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_description(sessiontype: Type[<a href="#class_ba_Session">ba.Session</a>]) -&gt; str </span></p>

<p style="padding-left: 60px;">Subclasses should override this to return a description for this
activity type (in English) within the context of the given
<a href="#class_ba_Session">ba.Session</a> type.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_GameActivity__get_description_display_string"><strong>get_description_display_string()</strong></a></h4>
<h5 style="padding-left: 60px;"><span style="color: #CC6600;"><em>&lt;class method&gt;</span></em></h5>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_description_display_string(sessiontype: Type[<a href="#class_ba_Session">ba.Session</a>]) -&gt; <a href="#class_ba_Lstr">ba.Lstr</a> </span></p>

<p style="padding-left: 60px;">Return a translated version of get_description().</p>

<p style="padding-left: 60px;">Sub-classes should override get_description(); not this.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_GameActivity__get_display_string"><strong>get_display_string()</strong></a></h4>
<h5 style="padding-left: 60px;"><span style="color: #CC6600;"><em>&lt;class method&gt;</span></em></h5>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_display_string(settings: Optional[Dict] = None) -&gt; <a href="#class_ba_Lstr">ba.Lstr</a> </span></p>

<p style="padding-left: 60px;">Return a descriptive name for this game/settings combo.</p>

<p style="padding-left: 60px;">Subclasses should override get_name(); not this.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_GameActivity__get_instance_description"><strong>get_instance_description()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_instance_description(self) -&gt; Union[str, Sequence]</span></p>

<p style="padding-left: 60px;">Return a description for this game instance, in English.</p>

<p style="padding-left: 60px;">This is shown in the center of the screen below the game name at the
start of a game. It should start with a capital letter and end with a
period, and can be a bit more verbose than the version returned by
get_instance_scoreboard_description().</p>

<p style="padding-left: 60px;">Note that translation is applied by looking up the specific returned
value as a key, so the number of returned variations should be limited;
ideally just one or two. To include arbitrary values in the
description, you can return a sequence of values in the following
form instead of just a string:</p>

<pre style="padding-left: 60px;"><span style="color: #008800;"># this will give us something like 'Score 3 goals.' in English</span>
<span style="color: #008800;"># and can properly translate to 'Anota 3 goles.' in Spanish.</span>
<span style="color: #008800;"># If we just returned the string 'Score 3 Goals' here, there would</span>
<span style="color: #008800;"># have to be a translation entry for each specific number. ew.</span>
return ['Score ${ARG1} goals.', self.settings['Score to Win']]</pre>

<p style="padding-left: 60px;">This way the first string can be consistently translated, with any arg
values then substituted into the result. ${ARG1} will be replaced with
the first value, ${ARG2} with the second, etc.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_GameActivity__get_instance_display_string"><strong>get_instance_display_string()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_instance_display_string(self) -&gt; <a href="#class_ba_Lstr">ba.Lstr</a></span></p>

<p style="padding-left: 60px;">Return a name for this particular game instance.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_GameActivity__get_instance_scoreboard_description"><strong>get_instance_scoreboard_description()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_instance_scoreboard_description(self) -&gt; Union[str, Sequence]</span></p>

<p style="padding-left: 60px;">Return a short description for this game instance in English.</p>

<p style="padding-left: 60px;">This description is used above the game scoreboard in the
corner of the screen, so it should be as concise as possible.
It should be lowercase and should not contain periods or other
punctuation.</p>

<p style="padding-left: 60px;">Note that translation is applied by looking up the specific returned
value as a key, so the number of returned variations should be limited;
ideally just one or two. To include arbitrary values in the
description, you can return a sequence of values in the following form
instead of just a string:</p>

<pre style="padding-left: 60px;"><span style="color: #008800;"># this will give us something like 'score 3 goals' in English</span>
<span style="color: #008800;"># and can properly translate to 'anota 3 goles' in Spanish.</span>
<span style="color: #008800;"># If we just returned the string 'score 3 goals' here, there would</span>
<span style="color: #008800;"># have to be a translation entry for each specific number. ew.</span>
return ['score ${ARG1} goals', self.settings['Score to Win']]</pre>

<p style="padding-left: 60px;">This way the first string can be consistently translated, with any arg
values then substituted into the result. ${ARG1} will be replaced
with the first value, ${ARG2} with the second, etc.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_GameActivity__get_instance_scoreboard_display_string"><strong>get_instance_scoreboard_display_string()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_instance_scoreboard_display_string(self) -&gt; <a href="#class_ba_Lstr">ba.Lstr</a></span></p>

<p style="padding-left: 60px;">Return a name for this particular game instance.</p>

<p style="padding-left: 60px;">This name is used above the game scoreboard in the corner
of the screen, so it should be as concise as possible.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_GameActivity__get_name"><strong>get_name()</strong></a></h4>
<h5 style="padding-left: 60px;"><span style="color: #CC6600;"><em>&lt;class method&gt;</span></em></h5>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_name() -&gt; str </span></p>

<p style="padding-left: 60px;">Return a str name for this game type.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_GameActivity__get_resolved_score_info"><strong>get_resolved_score_info()</strong></a></h4>
<h5 style="padding-left: 60px;"><span style="color: #CC6600;"><em>&lt;class method&gt;</span></em></h5>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_resolved_score_info() -&gt; Dict[str, Any] </span></p>

<p style="padding-left: 60px;">Call this to return a game's score info with all missing values
filled in with defaults. This should not be overridden; override
get_score_info() instead.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_GameActivity__get_score_info"><strong>get_score_info()</strong></a></h4>
<h5 style="padding-left: 60px;"><span style="color: #CC6600;"><em>&lt;class method&gt;</span></em></h5>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_score_info() -&gt; Dict[str, Any] </span></p>

<p style="padding-left: 60px;">Return info about game scoring setup; should be overridden by games.</p>

<p style="padding-left: 60px;">They should return a dict containing any of the following (missing
values will be default):</p>

<p style="padding-left: 60px;">'score_name': a label shown to the user for scores; 'Score',
    'Time Survived', etc. 'Score' is the default.</p>

<p style="padding-left: 60px;">'lower_is_better': a boolean telling whether lower scores are
    preferable instead of higher (the default).</p>

<p style="padding-left: 60px;">'none_is_winner': specifies whether a score value of None is considered
    better than other scores or worse. Default is False.</p>

<p style="padding-left: 60px;">'score_type': can be 'seconds', 'milliseconds', or 'points'.</p>

<p style="padding-left: 60px;">'score_version': to change high-score lists used by a game without
    renaming the game, change this. Defaults to empty string.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_GameActivity__get_settings"><strong>get_settings()</strong></a></h4>
<h5 style="padding-left: 60px;"><span style="color: #CC6600;"><em>&lt;class method&gt;</span></em></h5>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_settings(sessiontype: Type[<a href="#class_ba_Session">ba.Session</a>]) -&gt; List[Tuple[str, Dict[str, Any]]] </span></p>

<p style="padding-left: 60px;">Called by the default <a href="#method_ba_GameActivity__create_config_ui">ba.GameActivity.create_config_ui</a>()
implementation; should return a dict of config options to be presented
to the user for the given <a href="#class_ba_Session">ba.Session</a> type.</p>

<p style="padding-left: 60px;">The format for settings is a list of 2-member tuples consisting
of a name and a dict of options.</p>

<p style="padding-left: 60px;"><strong>Available Setting Options:</strong></p>

<p style="padding-left: 60px;">'default': This determines the default value as well as the
    type (int, float, or bool)</p>

<p style="padding-left: 60px;">'min_value': Minimum value for int/float settings.</p>

<p style="padding-left: 60px;">'max_value': Maximum value for int/float settings.</p>

<p style="padding-left: 60px;">'choices': A list of name/value pairs the user can choose from by name.</p>

<p style="padding-left: 60px;">'increment': Value increment for int/float settings.</p>

<pre style="padding-left: 60px;"><span style="color: #008800;"># example get_settings() implementation for a capture-the-flag game:</span>
@classmethod
def get_settings(cls,sessiontype):
    return [("Score to Win", {
                'default': 3,
                'min_value': 1
            }),
            ("Flag Touch Return Time", {
                'default': 0,
                'min_value': 0,
                'increment': 1
            }),
            ("Flag Idle Return Time", {
                'default': 30,
                'min_value': 5,
                'increment': 5
            }),
            ("Time Limit", {
                'default': 0,
                'choices': [
                    ('None', 0), ('1 Minute', 60), ('2 Minutes', 120),
                    ('5 Minutes', 300), ('10 Minutes', 600),
                    ('20 Minutes', 1200)
                ]
            }),
            ("Respawn Times", {
                'default': 1.0,
                'choices': [
                    ('Shorter', 0.25), ('Short', 0.5), ('Normal', 1.0),
                    ('Long', 2.0), ('Longer', 4.0)
                ]
            }),
            ("Epic Mode", {
                'default': False
            })]</pre>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_GameActivity__get_supported_maps"><strong>get_supported_maps()</strong></a></h4>
<h5 style="padding-left: 60px;"><span style="color: #CC6600;"><em>&lt;class method&gt;</span></em></h5>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_supported_maps(sessiontype: Type[<a href="#class_ba_Session">ba.Session</a>]) -&gt; List[str] </span></p>

<p style="padding-left: 60px;">Called by the default <a href="#method_ba_GameActivity__create_config_ui">ba.GameActivity.create_config_ui</a>()
implementation; should return a list of map names valid
for this game-type for the given <a href="#class_ba_Session">ba.Session</a> type.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_GameActivity__get_team_display_string"><strong>get_team_display_string()</strong></a></h4>
<h5 style="padding-left: 60px;"><span style="color: #CC6600;"><em>&lt;class method&gt;</span></em></h5>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_team_display_string(name: str) -&gt; <a href="#class_ba_Lstr">ba.Lstr</a> </span></p>

<p style="padding-left: 60px;">Given a team name, returns a localized version of it.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_GameActivity__handlemessage"><strong>handlemessage()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">handlemessage(self, msg: Any) -&gt; Any</span></p>

<p style="padding-left: 60px;">General message handling; can be passed any <a href="#class_category_Message_Classes">message object</a>.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_GameActivity__is_waiting_for_continue"><strong>is_waiting_for_continue()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">is_waiting_for_continue(self) -&gt; bool</span></p>

<p style="padding-left: 60px;">Returns whether or not this activity is currently waiting for the
player to continue (or timeout)</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_GameActivity__on_begin"><strong>on_begin()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">on_begin(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Called once the previous <a href="#class_ba_Activity">ba.Activity</a> has finished transitioning out.</p>

<p style="padding-left: 60px;">At this point the activity's initial players and teams are filled in
and it should begin its actual game logic.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_GameActivity__on_continue"><strong>on_continue()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">on_continue(self) -&gt; None</span></p>

<p style="padding-left: 60px;">This is called if a game supports and offers a continue and the player
accepts.  In this case the player should be given an extra life or
whatever is relevant to keep the game going.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_GameActivity__on_player_join"><strong>on_player_join()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">on_player_join(self, player: <a href="#class_ba_Player">ba.Player</a>) -&gt; None</span></p>

<p style="padding-left: 60px;">Called when a new <a href="#class_ba_Player">ba.Player</a> has joined the Activity.</p>

<p style="padding-left: 60px;">(including the initial set of Players)</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_GameActivity__on_player_leave"><strong>on_player_leave()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">on_player_leave(self, player: <a href="#class_ba_Player">ba.Player</a>) -&gt; None</span></p>

<p style="padding-left: 60px;">Called when a <a href="#class_ba_Player">ba.Player</a> is leaving the Activity.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_GameActivity__on_transition_in"><strong>on_transition_in()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">on_transition_in(self, music: str = None) -&gt; None</span></p>

<p style="padding-left: 60px;">Method override; optionally can
be passed a 'music' string which is the suggested type of
music to play during the game.
Note that in some cases music may be overridden by
the map or other factors, which is why you should pass
it in here instead of simply playing it yourself.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_GameActivity__project_flag_stand"><strong>project_flag_stand()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">project_flag_stand(self, pos: Sequence[float]) -&gt; None</span></p>

<p style="padding-left: 60px;">Project a flag-stand onto the ground at the given position.</p>

<p style="padding-left: 60px;">Useful for games such as capture-the-flag to show where a
movable flag originated from.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_GameActivity__respawn_player"><strong>respawn_player()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">respawn_player(self, player: <a href="#class_ba_Player">ba.Player</a>, respawn_time: Optional[float] = None) -&gt; None</span></p>

<p style="padding-left: 60px;">Given a <a href="#class_ba_Player">ba.Player</a>, sets up a standard respawn timer,
along with the standard counter display, etc.
At the end of the respawn period spawn_player() will
be called if the Player still exists.
An explicit 'respawn_time' can optionally be provided
(in seconds).</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_GameActivity__setup_standard_powerup_drops"><strong>setup_standard_powerup_drops()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">setup_standard_powerup_drops(self, enable_tnt: bool = True) -&gt; None</span></p>

<p style="padding-left: 60px;">Create standard powerup drops for the current map.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_GameActivity__setup_standard_time_limit"><strong>setup_standard_time_limit()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">setup_standard_time_limit(self, duration: float) -&gt; None</span></p>

<p style="padding-left: 60px;">Create a standard game time-limit given the provided
duration in seconds.
This will be displayed at the top of the screen.
If the time-limit expires, end_game() will be called.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_GameActivity__show_info"><strong>show_info()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">show_info(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Show the game description.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_GameActivity__show_scoreboard_info"><strong>show_scoreboard_info()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">show_scoreboard_info(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Create the game info display.</p>

<p style="padding-left: 60px;">This is the thing in the top left corner showing the name
and short description of the game.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_GameActivity__show_zoom_message"><strong>show_zoom_message()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">show_zoom_message(self, message: <a href="#class_ba_Lstr">ba.Lstr</a>, color: Sequence[float] = (0.9, 0.4, 0.0), scale: float = 0.8, duration: float = 2.0, trail: bool = False) -&gt; None</span></p>

<p style="padding-left: 60px;">Zooming text used to announce game names and winners.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_GameActivity__spawn_player"><strong>spawn_player()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">spawn_player(self, player: <a href="#class_ba_Player">ba.Player</a>) -&gt; <a href="#class_ba_Actor">ba.Actor</a></span></p>

<p style="padding-left: 60px;">Spawn *something* for the provided <a href="#class_ba_Player">ba.Player</a>.</p>

<p style="padding-left: 60px;">The default implementation simply calls spawn_player_spaz().</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_GameActivity__spawn_player_if_exists"><strong>spawn_player_if_exists()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">spawn_player_if_exists(self, player: <a href="#class_ba_Player">ba.Player</a>) -&gt; None</span></p>

<p style="padding-left: 60px;">A utility method which calls self.spawn_player() *only* if the
<a href="#class_ba_Player">ba.Player</a> provided still exists; handy for use in timers and whatnot.</p>

<p style="padding-left: 60px;">There is no need to override this; just override spawn_player().</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_GameActivity__spawn_player_spaz"><strong>spawn_player_spaz()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">spawn_player_spaz(self, player: <a href="#class_ba_Player">ba.Player</a>, position: Sequence[float] = (0, 0, 0), angle: float = None) -&gt; PlayerSpaz</span></p>

<p style="padding-left: 60px;">Create and wire up a ba.PlayerSpaz for the provided <a href="#class_ba_Player">ba.Player</a>.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_GameActivity__supports_session_type"><strong>supports_session_type()</strong></a></h4>
<h5 style="padding-left: 60px;"><span style="color: #CC6600;"><em>&lt;class method&gt;</span></em></h5>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">supports_session_type(sessiontype: Type[<a href="#class_ba_Session">ba.Session</a>]) -&gt; bool </span></p>

<p style="padding-left: 60px;">Return whether this game supports the provided Session type.</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_HitMessage">ba.HitMessage</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">Tells an object it has been hit in some way.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Message_Classes">Message Classes</a></p>

<p style="padding-left: 30px;">    This is used by punches, explosions, etc to convey
    their effect to a target.
</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_HitMessage____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.HitMessage(srcnode: '<a href="#class_ba_Node">ba.Node</a>' = None, pos: 'Sequence[float]' = None, velocity: 'Sequence[float]' = None, magnitude: 'float' = 1.0, velocity_magnitude: 'float' = 0.0, radius: 'float' = 1.0, source_player: '<a href="#class_ba_Player">ba.Player</a>' = None, kick_back: 'float' = 1.0, flat_damage: 'float' = None, hit_type: 'str' = 'generic', force_direction: 'Sequence[float]' = None, hit_subtype: 'str' = 'default')</span></p>

<p style="padding-left: 60px;">Instantiate a message with given values.</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_ImpactDamageMessage">ba.ImpactDamageMessage</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">Tells an object that it has been jarred violently.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Message_Classes">Message Classes</a></p>

<h3 style="padding-left: 0px;">Attributes:</h3>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_ImpactDamageMessage__intensity"><strong>intensity</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">float</span></p>
<p style="padding-left: 60px;">The intensity of the impact.</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_ImpactDamageMessage____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.ImpactDamageMessage(intensity: float)</span></p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_InputDevice">ba.InputDevice</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">An input-device such as a gamepad, touchscreen, or keyboard.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a></p>

<h3 style="padding-left: 0px;">Attributes:</h3>
<h5 style="padding-left: 30px;"><a href="#attr_ba_InputDevice__allows_configuring">allows_configuring</a>, <a href="#attr_ba_InputDevice__client_id">client_id</a>, <a href="#attr_ba_InputDevice__exists">exists</a>, <a href="#attr_ba_InputDevice__id">id</a>, <a href="#attr_ba_InputDevice__instance_number">instance_number</a>, <a href="#attr_ba_InputDevice__is_controller_app">is_controller_app</a>, <a href="#attr_ba_InputDevice__is_remote_client">is_remote_client</a>, <a href="#attr_ba_InputDevice__name">name</a>, <a href="#attr_ba_InputDevice__player">player</a>, <a href="#attr_ba_InputDevice__unique_identifier">unique_identifier</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_InputDevice__allows_configuring"><strong>allows_configuring</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"> bool</span></p>
<p style="padding-left: 60px;">Whether the input-device can be configured.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_InputDevice__client_id"><strong>client_id</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"> int</span></p>
<p style="padding-left: 60px;">The numeric client-id this device is associated with.
This is only meaningful for remote client inputs; for
all local devices this will be -1.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_InputDevice__exists"><strong>exists</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"> bool</span></p>
<p style="padding-left: 60px;">Whether the underlying device for this object is still present.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_InputDevice__id"><strong>id</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"> int</span></p>
<p style="padding-left: 60px;">The unique numeric id of this device.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_InputDevice__instance_number"><strong>instance_number</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"> int</span></p>
<p style="padding-left: 60px;">The number of this device among devices of the same type.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_InputDevice__is_controller_app"><strong>is_controller_app</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"> bool</span></p>
<p style="padding-left: 60px;">Whether this input-device represents a locally-connected
controller-app.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_InputDevice__is_remote_client"><strong>is_remote_client</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"> bool</span></p>
<p style="padding-left: 60px;">Whether this input-device represents a remotely-connected
client.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_InputDevice__name"><strong>name</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"> str</span></p>
<p style="padding-left: 60px;">The name of the device.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_InputDevice__player"><strong>player</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"> Optional[<a href="#class_ba_Player">ba.Player</a>]</span></p>
<p style="padding-left: 60px;">The player associated with this input device.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_InputDevice__unique_identifier"><strong>unique_identifier</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"> str</span></p>
<p style="padding-left: 60px;">A string that can be used to persistently identify the device,
even among other devices of the same type. Used for saving
prefs, etc.</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_InputDevice__get_account_name">get_account_name()</a>, <a href="#method_ba_InputDevice__get_axis_name">get_axis_name()</a>, <a href="#method_ba_InputDevice__get_button_name">get_button_name()</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_InputDevice__get_account_name"><strong>get_account_name()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_account_name(full: bool) -&gt; str</span></p>

<p style="padding-left: 60px;">Returns the account name associated with this device.</p>

<p style="padding-left: 60px;">(can be used to get account names for remote players)</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_InputDevice__get_axis_name"><strong>get_axis_name()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_axis_name(axis_id: int) -&gt; str</span></p>

<p style="padding-left: 60px;">Given an axis ID, returns the name of the axis on this device.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_InputDevice__get_button_name"><strong>get_button_name()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_button_name(button_id: int) -&gt; str</span></p>

<p style="padding-left: 60px;">Given a button ID, returns the name of the key/button on this device.</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_InputDeviceNotFoundError">ba.InputDeviceNotFoundError</a></strong></h3>
<p style="padding-left: 30px;">inherits from: <a href="#class_ba_NotFoundError">ba.NotFoundError</a>, Exception, BaseException</p>
<p style="padding-left: 30px;">Exception raised when an expected <a href="#class_ba_InputDevice">ba.InputDevice</a> does not exist.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Exception_Classes">Exception Classes</a>
</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<p style="padding-left: 30px;">&lt;all methods inherited from <a href="#class_ba_NotFoundError">ba.NotFoundError</a>&gt;</p>
<hr>
<h2><strong><a class="offsanchor" name="class_ba_Level">ba.Level</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">An entry in a <a href="#class_ba_Campaign">ba.Campaign</a> consisting of a name, game type, and settings.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a>
</p>

<h3 style="padding-left: 0px;">Attributes:</h3>
<h5 style="padding-left: 30px;"><a href="#attr_ba_Level__complete">complete</a>, <a href="#attr_ba_Level__displayname">displayname</a>, <a href="#attr_ba_Level__gametype">gametype</a>, <a href="#attr_ba_Level__index">index</a>, <a href="#attr_ba_Level__name">name</a>, <a href="#attr_ba_Level__preview_texture_name">preview_texture_name</a>, <a href="#attr_ba_Level__rating">rating</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Level__complete"><strong>complete</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">bool</span></p>
<p style="padding-left: 60px;">Whether this Level has been completed.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Level__displayname"><strong>displayname</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"><a href="#class_ba_Lstr">ba.Lstr</a></span></p>
<p style="padding-left: 60px;">The localized name for this Level.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Level__gametype"><strong>gametype</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">Type[<a href="#class_ba_GameActivity">ba.GameActivity</a>]</span></p>
<p style="padding-left: 60px;">The type of game used for this Level.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Level__index"><strong>index</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">int</span></p>
<p style="padding-left: 60px;">The zero-based index of this Level in its <a href="#class_ba_Campaign">ba.Campaign</a>.</p>

<p style="padding-left: 60px;">        Access results in a RuntimeError if the Level is  not assigned to a
        Campaign.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Level__name"><strong>name</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">str</span></p>
<p style="padding-left: 60px;">The unique name for this Level.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Level__preview_texture_name"><strong>preview_texture_name</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">str</span></p>
<p style="padding-left: 60px;">The preview texture name for this Level.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Level__rating"><strong>rating</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">float</span></p>
<p style="padding-left: 60px;">The current rating for this Level.</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_Level____init__">&lt;constructor&gt;</a>, <a href="#method_ba_Level__get_campaign">get_campaign()</a>, <a href="#method_ba_Level__get_high_scores">get_high_scores()</a>, <a href="#method_ba_Level__get_preview_texture">get_preview_texture()</a>, <a href="#method_ba_Level__get_score_version_string">get_score_version_string()</a>, <a href="#method_ba_Level__get_settings">get_settings()</a>, <a href="#method_ba_Level__set_complete">set_complete()</a>, <a href="#method_ba_Level__set_high_scores">set_high_scores()</a>, <a href="#method_ba_Level__set_rating">set_rating()</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Level____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.Level(name: str, gametype: Type[<a href="#class_ba_GameActivity">ba.GameActivity</a>], settings: Dict[str, Any], preview_texture_name: str, displayname: str = None)</span></p>

<p style="padding-left: 60px;">Initializes a Level object with the provided values.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Level__get_campaign"><strong>get_campaign()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_campaign(self) -&gt; Optional[<a href="#class_ba_Campaign">ba.Campaign</a>]</span></p>

<p style="padding-left: 60px;">Return the <a href="#class_ba_Campaign">ba.Campaign</a> this Level is associated with, or None.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Level__get_high_scores"><strong>get_high_scores()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_high_scores(self) -&gt; Dict</span></p>

<p style="padding-left: 60px;">Return the current high scores for this Level.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Level__get_preview_texture"><strong>get_preview_texture()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_preview_texture(self) -&gt; <a href="#class_ba_Texture">ba.Texture</a></span></p>

<p style="padding-left: 60px;">Load/return the preview Texture for this Level.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Level__get_score_version_string"><strong>get_score_version_string()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_score_version_string(self) -&gt; str</span></p>

<p style="padding-left: 60px;">Return the score version string for this Level.</p>

<p style="padding-left: 60px;">If a Level's gameplay changes significantly, its version string
can be changed to separate its new high score lists/etc. from the old.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Level__get_settings"><strong>get_settings()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_settings(self) -&gt; Dict[str, Any]</span></p>

<p style="padding-left: 60px;">Returns the settings for this Level.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Level__set_complete"><strong>set_complete()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">set_complete(self, val: bool) -&gt; None</span></p>

<p style="padding-left: 60px;">Set whether or not this level is complete.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Level__set_high_scores"><strong>set_high_scores()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">set_high_scores(self, high_scores: Dict) -&gt; None</span></p>

<p style="padding-left: 60px;">Set high scores for this level.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Level__set_rating"><strong>set_rating()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">set_rating(self, rating: float) -&gt; None</span></p>

<p style="padding-left: 60px;">Set a rating for this Level, replacing the old ONLY IF higher.</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_Lobby">ba.Lobby</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">Container for choosers.</p>

<h3 style="padding-left: 0px;">Attributes:</h3>
<h5 style="padding-left: 30px;"><a href="#attr_ba_Lobby__teams">teams</a>, <a href="#attr_ba_Lobby__use_team_colors">use_team_colors</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Lobby__teams"><strong>teams</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">List[<a href="#class_ba_Team">ba.Team</a>]</span></p>
<p style="padding-left: 60px;">Teams available in this lobby.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Lobby__use_team_colors"><strong>use_team_colors</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">bool</span></p>
<p style="padding-left: 60px;">A bool for whether this lobby is using team colors.</p>

<p style="padding-left: 60px;">        If False, inidividual player colors are used instead.</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_Lobby____init__">&lt;constructor&gt;</a>, <a href="#method_ba_Lobby__add_chooser">add_chooser()</a>, <a href="#method_ba_Lobby__check_all_ready">check_all_ready()</a>, <a href="#method_ba_Lobby__create_join_info">create_join_info()</a>, <a href="#method_ba_Lobby__get_choosers">get_choosers()</a>, <a href="#method_ba_Lobby__reload_profiles">reload_profiles()</a>, <a href="#method_ba_Lobby__remove_all_choosers">remove_all_choosers()</a>, <a href="#method_ba_Lobby__remove_all_choosers_and_kick_players">remove_all_choosers_and_kick_players()</a>, <a href="#method_ba_Lobby__remove_chooser">remove_chooser()</a>, <a href="#method_ba_Lobby__update_positions">update_positions()</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Lobby____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.Lobby()</span></p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Lobby__add_chooser"><strong>add_chooser()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">add_chooser(self, player: <a href="#class_ba_Player">ba.Player</a>) -&gt; None</span></p>

<p style="padding-left: 60px;">Add a chooser to the lobby for the provided player.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Lobby__check_all_ready"><strong>check_all_ready()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">check_all_ready(self) -&gt; bool</span></p>

<p style="padding-left: 60px;">Return whether all choosers are marked ready.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Lobby__create_join_info"><strong>create_join_info()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">create_join_info(self) -&gt; JoinInfo</span></p>

<p style="padding-left: 60px;">Create a display of on-screen information for joiners.</p>

<p style="padding-left: 60px;">(how to switch teams, players, etc.)
Intended for use in initial joining-screens.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Lobby__get_choosers"><strong>get_choosers()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_choosers(self) -&gt; List[Chooser]</span></p>

<p style="padding-left: 60px;">Return the lobby's current choosers.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Lobby__reload_profiles"><strong>reload_profiles()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">reload_profiles(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Reload available player profiles.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Lobby__remove_all_choosers"><strong>remove_all_choosers()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">remove_all_choosers(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Remove all choosers without kicking players.</p>

<p style="padding-left: 60px;">This is called after all players check in and enter a game.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Lobby__remove_all_choosers_and_kick_players"><strong>remove_all_choosers_and_kick_players()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">remove_all_choosers_and_kick_players(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Remove all player choosers and kick attached players.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Lobby__remove_chooser"><strong>remove_chooser()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">remove_chooser(self, player: <a href="#class_ba_Player">ba.Player</a>) -&gt; None</span></p>

<p style="padding-left: 60px;">Remove a single player's chooser; does not kick him.</p>

<p style="padding-left: 60px;">This is used when a player enters the game and no longer
needs a chooser.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Lobby__update_positions"><strong>update_positions()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">update_positions(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Update positions for all choosers.</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_Lstr">ba.Lstr</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">Used to specify strings in a language-independent way.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_General_Utility_Classes">General Utility Classes</a></p>

<p style="padding-left: 30px;">    These should be used whenever possible in place of hard-coded strings
    so that in-game or UI elements show up correctly on all clients in their
    currently-active language.</p>

<p style="padding-left: 30px;">    To see available resource keys, look at any of the bs_language_*.py files
    in the game or the translations pages at bombsquadgame.com/translate.</p>

<pre style="padding-left: 30px;"><span style="color: #008800;">    # EXAMPLE 1: specify a string from a resource path</span>
    mynode.text = <a href="#class_ba_Lstr">ba.Lstr</a>(resource='audioSettingsWindow.titleText')</pre>

<pre style="padding-left: 30px;"><span style="color: #008800;">    # EXAMPLE 2: specify a translated string via a category and english value;</span>
<span style="color: #008800;">    # if a translated value is available, it will be used; otherwise the</span>
<span style="color: #008800;">    # english value will be. To see available translation categories, look</span>
<span style="color: #008800;">    # under the 'translations' resource section.</span>
    mynode.text = <a href="#class_ba_Lstr">ba.Lstr</a>(translate=('gameDescriptions', 'Defeat all enemies'))</pre>

<pre style="padding-left: 30px;"><span style="color: #008800;">    # EXAMPLE 3: specify a raw value and some substitutions.  Substitutions can</span>
<span style="color: #008800;">    # be used with resource and translate modes as well.</span>
    mynode.text = <a href="#class_ba_Lstr">ba.Lstr</a>(value='${A} / ${B}',
                          subs=[('${A}', str(score)), ('${B}', str(total))])</pre>

<pre style="padding-left: 30px;"><span style="color: #008800;">    # EXAMPLE 4: Lstrs can be nested.  This example would display the resource</span>
<span style="color: #008800;">    # at res_a but replace ${NAME} with the value of the resource at res_b</span>
    mytextnode.text = <a href="#class_ba_Lstr">ba.Lstr</a>(resource='res_a',
                              subs=[('${NAME}', <a href="#class_ba_Lstr">ba.Lstr</a>(resource='res_b'))])
</pre>

<h3 style="padding-left: 0px;">Methods:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_Lstr____init__">&lt;constructor&gt;</a>, <a href="#method_ba_Lstr__evaluate">evaluate()</a>, <a href="#method_ba_Lstr__is_flat_value">is_flat_value()</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Lstr____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.Lstr(*args: Any, **keywds: Any)</span></p>

<p style="padding-left: 60px;">Instantiate a Lstr.</p>

<p style="padding-left: 60px;">Pass a value for either 'resource', 'translate',
or 'value'. (see Lstr help for examples).
'subs' can be a sequence of 2-member sequences consisting of values
and replacements.
'fallback_resource' can be a resource key that will be used if the
main one is not present for
the current language in place of falling back to the english value
('resource' mode only).
'fallback_value' can be a literal string that will be used if neither
the resource nor the fallback resource is found ('resource' mode only).</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Lstr__evaluate"><strong>evaluate()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">evaluate(self) -&gt; str</span></p>

<p style="padding-left: 60px;">Evaluate the Lstr and returns a flat string in the current language.</p>

<p style="padding-left: 60px;">You should avoid doing this as much as possible and instead pass
and store Lstr values.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Lstr__is_flat_value"><strong>is_flat_value()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">is_flat_value(self) -&gt; bool</span></p>

<p style="padding-left: 60px;">Return whether the Lstr is a 'flat' value.</p>

<p style="padding-left: 60px;">This is defined as a simple string value incorporating no translations,
resources, or substitutions.  In this case it may be reasonable to
replace it with a raw string value, perform string manipulation on it,
etc.</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_Map">ba.Map</a></strong></h3>
<p style="padding-left: 30px;">inherits from: <a href="#class_ba_Actor">ba.Actor</a></p>
<p style="padding-left: 30px;">A game map.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a></p>

<p style="padding-left: 30px;">    Consists of a collection of terrain nodes, metadata, and other
    functionality comprising a game map.
</p>

<h3 style="padding-left: 0px;">Attributes:</h3>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Map__activity"><strong>activity</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"><a href="#class_ba_Activity">ba.Activity</a></span></p>
<p style="padding-left: 60px;">The Activity this Actor was created in.</p>

<p style="padding-left: 60px;">        Raises a <a href="#class_ba_ActivityNotFoundError">ba.ActivityNotFoundError</a> if the Activity no longer exists.</p>

<h3 style="padding-left: 0px;">Methods Inherited:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_Actor__autoretain">autoretain()</a>, <a href="#method_ba_Actor__exists">exists()</a>, <a href="#method_ba_Actor__getactivity">getactivity()</a>, <a href="#method_ba_Actor__is_alive">is_alive()</a>, <a href="#method_ba_Actor__is_expired">is_expired()</a>, <a href="#method_ba_Actor__on_expire">on_expire()</a></h5>
<h3 style="padding-left: 0px;">Methods Defined or Overridden:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_Map____init__">&lt;constructor&gt;</a>, <a href="#method_ba_Map__get_def_bound_box">get_def_bound_box()</a>, <a href="#method_ba_Map__get_def_point">get_def_point()</a>, <a href="#method_ba_Map__get_def_points">get_def_points()</a>, <a href="#method_ba_Map__get_ffa_start_position">get_ffa_start_position()</a>, <a href="#method_ba_Map__get_flag_position">get_flag_position()</a>, <a href="#method_ba_Map__get_music_type">get_music_type()</a>, <a href="#method_ba_Map__get_name">get_name()</a>, <a href="#method_ba_Map__get_play_types">get_play_types()</a>, <a href="#method_ba_Map__get_preview_texture_name">get_preview_texture_name()</a>, <a href="#method_ba_Map__get_start_position">get_start_position()</a>, <a href="#method_ba_Map__handlemessage">handlemessage()</a>, <a href="#method_ba_Map__is_point_near_edge">is_point_near_edge()</a>, <a href="#method_ba_Map__on_preload">on_preload()</a>, <a href="#method_ba_Map__preload">preload()</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Map____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.Map(vr_overlay_offset: Optional[Sequence[float]] = None)</span></p>

<p style="padding-left: 60px;">Instantiate a map.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Map__get_def_bound_box"><strong>get_def_bound_box()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_def_bound_box(self, name: str) -&gt; Optional[Tuple[float, float, float, float, float, float]]</span></p>

<p style="padding-left: 60px;">Return a 6 member bounds tuple or None if it is not defined.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Map__get_def_point"><strong>get_def_point()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_def_point(self, name: str) -&gt; Optional[Sequence[float]]</span></p>

<p style="padding-left: 60px;">Return a single defined point or a default value in its absence.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Map__get_def_points"><strong>get_def_points()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_def_points(self, name: str) -&gt; List[Sequence[float]]</span></p>

<p style="padding-left: 60px;">Return a list of named points.</p>

<p style="padding-left: 60px;">Return as many sequential ones are defined (flag1, flag2, flag3), etc.
If none are defined, returns an empty list.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Map__get_ffa_start_position"><strong>get_ffa_start_position()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_ffa_start_position(self, players: Sequence[<a href="#class_ba_Player">ba.Player</a>]) -&gt; Sequence[float]</span></p>

<p style="padding-left: 60px;">Return a random starting position in one of the FFA spawn areas.</p>

<p style="padding-left: 60px;">If a list of <a href="#class_ba_Player">ba.Players</a> is provided; the returned points will be
as far from these players as possible.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Map__get_flag_position"><strong>get_flag_position()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_flag_position(self, team_index: int = None) -&gt; Sequence[float]</span></p>

<p style="padding-left: 60px;">Return a flag position on the map for the given team index.</p>

<p style="padding-left: 60px;">Pass None to get the default flag point.
(used for things such as king-of-the-hill)</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Map__get_music_type"><strong>get_music_type()</strong></a></h4>
<h5 style="padding-left: 60px;"><span style="color: #CC6600;"><em>&lt;class method&gt;</span></em></h5>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_music_type() -&gt; Optional[str] </span></p>

<p style="padding-left: 60px;">Return a music-type string that should be played on this map.</p>

<p style="padding-left: 60px;">If None is returned, default music will be used.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Map__get_name"><strong>get_name()</strong></a></h4>
<h5 style="padding-left: 60px;"><span style="color: #CC6600;"><em>&lt;class method&gt;</span></em></h5>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_name() -&gt; str </span></p>

<p style="padding-left: 60px;">Return the unique name of this map, in English.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Map__get_play_types"><strong>get_play_types()</strong></a></h4>
<h5 style="padding-left: 60px;"><span style="color: #CC6600;"><em>&lt;class method&gt;</span></em></h5>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_play_types() -&gt; List[str] </span></p>

<p style="padding-left: 60px;">Return valid play types for this map.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Map__get_preview_texture_name"><strong>get_preview_texture_name()</strong></a></h4>
<h5 style="padding-left: 60px;"><span style="color: #CC6600;"><em>&lt;class method&gt;</span></em></h5>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_preview_texture_name() -&gt; Optional[str] </span></p>

<p style="padding-left: 60px;">Return the name of the preview texture for this map.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Map__get_start_position"><strong>get_start_position()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_start_position(self, team_index: int) -&gt; Sequence[float]</span></p>

<p style="padding-left: 60px;">Return a random starting position for the given team index.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Map__handlemessage"><strong>handlemessage()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">handlemessage(self, msg: Any) -&gt; Any</span></p>

<p style="padding-left: 60px;">General message handling; can be passed any <a href="#class_category_Message_Classes">message object</a>.</p>

<p style="padding-left: 60px;">The default implementation will handle <a href="#class_ba_DieMessage">ba.DieMessages</a> by
calling self.node.delete() if self contains a 'node' attribute.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Map__is_point_near_edge"><strong>is_point_near_edge()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">is_point_near_edge(self, point: <a href="#class_ba_Vec3">ba.Vec3</a>, running: bool = False) -&gt; bool</span></p>

<p style="padding-left: 60px;">Return whether the provided point is near an edge of the map.</p>

<p style="padding-left: 60px;">Simple bot logic uses this call to determine if they
are approaching a cliff or wall. If this returns True they will
generally not walk/run any farther away from the origin.
If 'running' is True, the buffer should be a bit larger.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Map__on_preload"><strong>on_preload()</strong></a></h4>
<h5 style="padding-left: 60px;"><span style="color: #CC6600;"><em>&lt;class method&gt;</span></em></h5>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">on_preload() -&gt; Any </span></p>

<p style="padding-left: 60px;">Called when the map is being preloaded.</p>

<p style="padding-left: 60px;">It should return any media/data it requires to operate</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Map__preload"><strong>preload()</strong></a></h4>
<h5 style="padding-left: 60px;"><span style="color: #CC6600;"><em>&lt;class method&gt;</span></em></h5>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">preload() -&gt; None </span></p>

<p style="padding-left: 60px;">Preload map media.</p>

<p style="padding-left: 60px;">This runs the class's on_preload() method as needed to prep it to run.
Preloading should generally be done in a <a href="#class_ba_Activity">ba.Activity</a>'s __init__ method.
Note that this is a classmethod since it is not operate on map
instances but rather on the class itself before instances are made</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_Material">ba.Material</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">Material(label: str = None)</p>

<p style="padding-left: 30px;">An entity applied to game objects to modify collision behavior.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a></p>

<p style="padding-left: 30px;">A material can affect physical characteristics, generate sounds,
or trigger callback functions when collisions occur.</p>

<p style="padding-left: 30px;">Materials are applied to 'parts', which are groups of one or more
rigid bodies created as part of a <a href="#class_ba_Node">ba.Node</a>.  Nodes can have any number
of parts, each with its own set of materials. Generally materials are
specified as array attributes on the Node. The 'spaz' node, for
example, has various attributes such as 'materials',
'roller_materials', and 'punch_materials', which correspond to the
various parts it creates.</p>

<p style="padding-left: 30px;">Use <a href="#class_ba_Material">ba.Material</a>() to instantiate a blank material, and then use its
add_actions() method to define what the material does.</p>

<h3 style="padding-left: 0px;">Attributes:</h3>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Material__label"><strong>label</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"> str</span></p>
<p style="padding-left: 60px;">A label for the material; only used for debugging.</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Material__add_actions"><strong>add_actions()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">add_actions(actions: Tuple, conditions: Optional[Tuple] = None)
  -&gt; None</span></p>

<p style="padding-left: 60px;">Add one or more actions to the material, optionally with conditions.</p>

<p style="padding-left: 60px;"><strong>Conditions:</strong></p>

<p style="padding-left: 60px;">Conditions are provided as tuples which can be combined to form boolean
logic. A single condition might look like ('condition_name', cond_arg),
or a more complex nested one might look like (('some_condition',
cond_arg), 'or', ('another_condition', cond2_arg)).</p>

<p style="padding-left: 60px;">'and', 'or', and 'xor' are available to chain together 2 conditions, as
  seen above.</p>

<p style="padding-left: 60px;"><strong>Available Conditions:</strong></p>

<p style="padding-left: 60px;">('they_have_material', material) - does the part we're hitting have a
  given <a href="#class_ba_Material">ba.Material</a>?</p>

<p style="padding-left: 60px;">('they_dont_have_material', material) - does the part we're hitting
  not have a given <a href="#class_ba_Material">ba.Material</a>?</p>

<p style="padding-left: 60px;">('eval_colliding') - is 'collide' true at this point in material
  evaluation? (see the modify_part_collision action)</p>

<p style="padding-left: 60px;">('eval_not_colliding') - is 'collide' false at this point in material
  evaluation? (see the modify_part_collision action)</p>

<p style="padding-left: 60px;">('we_are_younger_than', age) - is our part younger than 'age'
  (in milliseconds)?</p>

<p style="padding-left: 60px;">('we_are_older_than', age) - is our part older than 'age'
  (in milliseconds)?</p>

<p style="padding-left: 60px;">('they_are_younger_than', age) - is the part we're hitting younger than
  'age' (in milliseconds)?</p>

<p style="padding-left: 60px;">('they_are_older_than', age) - is the part we're hitting older than
  'age' (in milliseconds)?</p>

<p style="padding-left: 60px;">('they_are_same_node_as_us') - does the part we're hitting belong to
  the same <a href="#class_ba_Node">ba.Node</a> as us?</p>

<p style="padding-left: 60px;">('they_are_different_node_than_us') - does the part we're hitting
  belong to a different <a href="#class_ba_Node">ba.Node</a> than us?</p>

<p style="padding-left: 60px;"><strong>Actions:</strong></p>

<p style="padding-left: 60px;">In a similar manner, actions are specified as tuples. Multiple actions
can be specified by providing a tuple of tuples.</p>

<p style="padding-left: 60px;"><strong>Available Actions:</strong></p>

<p style="padding-left: 60px;">('call', when, callable) - calls the provided callable; 'when' can be
  either 'at_connect' or 'at_disconnect'. 'at_connect' means to fire
  when the two parts first come in contact; 'at_disconnect' means to
  fire once they cease being in contact.</p>

<p style="padding-left: 60px;">('message', who, when, message_obj) - sends a message object; 'who' can
  be either 'our_node' or 'their_node', 'when' can be 'at_connect' or
  'at_disconnect', and message_obj is the message object to send.
  This has the same effect as calling the node's handlemessage()
  method.</p>

<p style="padding-left: 60px;">('modify_part_collision', attr, value) - changes some characteristic
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

<p style="padding-left: 60px;">('modify_node_collision', attr, value) - similar to
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

<p style="padding-left: 60px;">('sound', sound, volume) - plays a <a href="#class_ba_Sound">ba.Sound</a> when a collision occurs, at
  a given volume, regardless of the collision speed/etc.</p>

<p style="padding-left: 60px;">('impact_sound', sound, targetImpulse, volume) - plays a sound when a
  collision occurs, based on the speed of impact. Provide a <a href="#class_ba_Sound">ba.Sound</a>, a
  target-impulse, and a volume.</p>

<p style="padding-left: 60px;">('skid_sound', sound, targetImpulse, volume) - plays a sound during a
  collision when parts are 'scraping' against each other. Provide a
  <a href="#class_ba_Sound">ba.Sound</a>, a target-impulse, and a volume.</p>

<p style="padding-left: 60px;">('roll_sound', sound, targetImpulse, volume) - plays a sound during a
  collision when parts are 'rolling' against each other. Provide a
  <a href="#class_ba_Sound">ba.Sound</a>, a target-impulse, and a volume.</p>

<pre style="padding-left: 60px;"><span style="color: #008800;"># example 1: create a material that lets us ignore</span>
<span style="color: #008800;"># collisions against any nodes we touch in the first</span>
<span style="color: #008800;"># 100 ms of our existence; handy for preventing us from</span>
<span style="color: #008800;"># exploding outward if we spawn on top of another object:</span>
m = <a href="#class_ba_Material">ba.Material</a>()
m.add_actions(conditions=(('we_are_younger_than', 100),
                         'or',('they_are_younger_than', 100)),
             actions=('modify_node_collision', 'collide', False))</pre>

<pre style="padding-left: 60px;"><span style="color: #008800;"># example 2: send a DieMessage to anything we touch, but cause</span>
<span style="color: #008800;"># no physical response.  This should cause any <a href="#class_ba_Actor">ba.Actor</a> to drop dead:</span>
m = <a href="#class_ba_Material">ba.Material</a>()
m.add_actions(actions=(('modify_part_collision', 'physical', False),
                      ('message', 'their_node', 'at_connect',
                       <a href="#class_ba_DieMessage">ba.DieMessage</a>())))</pre>

<pre style="padding-left: 60px;"><span style="color: #008800;"># example 3: play some sounds when we're contacting the ground:</span>
m = <a href="#class_ba_Material">ba.Material</a>()
m.add_actions(conditions=('they_have_material',
                          <a href="#function_ba_sharedobj">ba.sharedobj</a>('footing_material')),
              actions=(('impact_sound', <a href="#function_ba_getsound">ba.getsound</a>('metalHit'), 2, 5),
                       ('skid_sound', <a href="#function_ba_getsound">ba.getsound</a>('metalSkid'), 2, 5)))</pre>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_Model">ba.Model</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">A reference to a model.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Asset_Classes">Asset Classes</a></p>

<p style="padding-left: 30px;">Models are used for drawing.
Use <a href="#function_ba_getmodel">ba.getmodel</a>() to instantiate one.</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_MusicPlayer">ba.MusicPlayer</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">Wrangles soundtrack music playback.</p>

<p style="padding-left: 30px;">    Music can be played either through the game itself
    or via a platform-specific external player.
</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_MusicPlayer____init__">&lt;constructor&gt;</a>, <a href="#method_ba_MusicPlayer__on_play">on_play()</a>, <a href="#method_ba_MusicPlayer__on_select_entry">on_select_entry()</a>, <a href="#method_ba_MusicPlayer__on_set_volume">on_set_volume()</a>, <a href="#method_ba_MusicPlayer__on_shutdown">on_shutdown()</a>, <a href="#method_ba_MusicPlayer__on_stop">on_stop()</a>, <a href="#method_ba_MusicPlayer__play">play()</a>, <a href="#method_ba_MusicPlayer__select_entry">select_entry()</a>, <a href="#method_ba_MusicPlayer__set_volume">set_volume()</a>, <a href="#method_ba_MusicPlayer__shutdown">shutdown()</a>, <a href="#method_ba_MusicPlayer__stop">stop()</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_MusicPlayer____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.MusicPlayer()</span></p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_MusicPlayer__on_play"><strong>on_play()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">on_play(self, entry: Any) -&gt; None</span></p>

<p style="padding-left: 60px;">Called when a new song/playlist/etc should be played.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_MusicPlayer__on_select_entry"><strong>on_select_entry()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">on_select_entry(self, callback: Callable[[Any], None], current_entry: Any, selection_target_name: str) -&gt; Any</span></p>

<p style="padding-left: 60px;">Present a GUI to select an entry.</p>

<p style="padding-left: 60px;">The callback should be called with a valid entry or None to
signify that the default soundtrack should be used..</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_MusicPlayer__on_set_volume"><strong>on_set_volume()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">on_set_volume(self, volume: float) -&gt; None</span></p>

<p style="padding-left: 60px;">Called when the volume should be changed.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_MusicPlayer__on_shutdown"><strong>on_shutdown()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">on_shutdown(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Called on final app shutdown.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_MusicPlayer__on_stop"><strong>on_stop()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">on_stop(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Called when the music should stop.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_MusicPlayer__play"><strong>play()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">play(self, entry: Any) -&gt; None</span></p>

<p style="padding-left: 60px;">Play provided entry.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_MusicPlayer__select_entry"><strong>select_entry()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">select_entry(self, callback: Callable[[Any], None], current_entry: Any, selection_target_name: str) -&gt; Any</span></p>

<p style="padding-left: 60px;">Summons a UI to select a new soundtrack entry.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_MusicPlayer__set_volume"><strong>set_volume()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">set_volume(self, volume: float) -&gt; None</span></p>

<p style="padding-left: 60px;">Set player volume (value should be between 0 and 1).</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_MusicPlayer__shutdown"><strong>shutdown()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">shutdown(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Shutdown music playback completely.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_MusicPlayer__stop"><strong>stop()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">stop(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Stop any playback that is occurring.</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_Node">ba.Node</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">Reference to a Node; the low level building block of the game.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a></p>

<p style="padding-left: 30px;">At its core, a game is nothing more than a scene of Nodes
with attributes getting interconnected or set over time.</p>

<p style="padding-left: 30px;">A <a href="#class_ba_Node">ba.Node</a> instance should be thought of as a weak-reference
to a game node; *not* the node itself. This means a Node's
lifecycle is completely independent of how many Python references
to it exist. To explicitly add a new node to the game, use
<a href="#function_ba_newnode">ba.newnode</a>(), and to explicitly delete one, use <a href="#method_ba_Node__delete">ba.Node.delete</a>().
<a href="#method_ba_Node__exists">ba.Node.exists</a>() can be used to determine if a Node still points to
a live node in the game.</p>

<p style="padding-left: 30px;">You can use <a href="#class_ba_Node">ba.Node</a>(None) to instantiate an invalid
Node reference (sometimes used as attr values/etc).</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_Node__add_death_action">add_death_action()</a>, <a href="#method_ba_Node__connectattr">connectattr()</a>, <a href="#method_ba_Node__delete">delete()</a>, <a href="#method_ba_Node__exists">exists()</a>, <a href="#method_ba_Node__get_name">get_name()</a>, <a href="#method_ba_Node__getdelegate">getdelegate()</a>, <a href="#method_ba_Node__getnodetype">getnodetype()</a>, <a href="#method_ba_Node__handlemessage">handlemessage()</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Node__add_death_action"><strong>add_death_action()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">add_death_action(action: Callable[[], None]) -&gt; None</span></p>

<p style="padding-left: 60px;">Add a callable object to be called upon this node's death.
Note that these actions are run just after the node dies, not before.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Node__connectattr"><strong>connectattr()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">connectattr(srcattr: str, dstnode: Node, dstattr: str) -&gt; None</span></p>

<p style="padding-left: 60px;">Connect one of this node's attributes to an attribute on another node.
This will immediately set the target attribute's value to that of the
source attribute, and will continue to do so once per step as long as
the two nodes exist.  The connection can be severed by setting the
target attribute to any value or connecting another node attribute
to it.</p>

<pre style="padding-left: 60px;"><span style="color: #008800;"># example: create a locator and attach a light to it</span>
light = <a href="#function_ba_newnode">ba.newnode</a>('light')
loc = <a href="#function_ba_newnode">ba.newnode</a>('locator', attrs={'position': (0,10,0)})
loc.connectattr('position', light, 'position')</pre>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Node__delete"><strong>delete()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">delete(ignore_missing: bool = True) -&gt; None</span></p>

<p style="padding-left: 60px;">Delete the node.  Ignores already-deleted nodes unless ignore_missing
is False, in which case an Exception is thrown.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Node__exists"><strong>exists()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">exists() -&gt; bool</span></p>

<p style="padding-left: 60px;">Returns whether the Node still exists.
Most functionality will fail on a nonexistent Node, so it's never a bad
idea to check this.</p>

<p style="padding-left: 60px;">Note that you can also use the boolean operator for this same
functionality, so a statement such as "if mynode" will do
the right thing both for Node objects and values of None.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Node__get_name"><strong>get_name()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_name() -&gt; str</span></p>

<p style="padding-left: 60px;">Return the name assigned to a Node; used mainly for debugging</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Node__getdelegate"><strong>getdelegate()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">getdelegate() -&gt; Any</span></p>

<p style="padding-left: 60px;">Returns the node's current delegate, which is the Python object
designated to handle the Node's messages.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Node__getnodetype"><strong>getnodetype()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">getnodetype() -&gt; str</span></p>

<p style="padding-left: 60px;">Return the type of Node referenced by this object as a string.
(Note this is different from the Python type which is always <a href="#class_ba_Node">ba.Node</a>)</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Node__handlemessage"><strong>handlemessage()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">handlemessage(*args: Any) -&gt; None</span></p>

<p style="padding-left: 60px;">General message handling; can be passed any <a href="#class_category_Message_Classes">message object</a>.</p>

<p style="padding-left: 60px;">All standard message objects are forwarded along to the <a href="#class_ba_Node">ba.Node</a>'s
delegate for handling (generally the <a href="#class_ba_Actor">ba.Actor</a> that made the node).</p>

<p style="padding-left: 60px;"><a href="#class_ba_Node">ba.Nodes</a> are unique, however, in that they can be passed a second
form of message; 'node-messages'.  These consist of a string type-name
as a first argument along with the args specific to that type name
as additional arguments.
Node-messages communicate directly with the low-level node layer
and are delivered simultaneously on all game clients,
acting as an alternative to setting node attributes.</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_NodeNotFoundError">ba.NodeNotFoundError</a></strong></h3>
<p style="padding-left: 30px;">inherits from: <a href="#class_ba_NotFoundError">ba.NotFoundError</a>, Exception, BaseException</p>
<p style="padding-left: 30px;">Exception raised when an expected <a href="#class_ba_Node">ba.Node</a> does not exist.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Exception_Classes">Exception Classes</a>
</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<p style="padding-left: 30px;">&lt;all methods inherited from <a href="#class_ba_NotFoundError">ba.NotFoundError</a>&gt;</p>
<hr>
<h2><strong><a class="offsanchor" name="class_ba_NotFoundError">ba.NotFoundError</a></strong></h3>
<p style="padding-left: 30px;">inherits from: Exception, BaseException</p>
<p style="padding-left: 30px;">Exception raised when a referenced object does not exist.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Exception_Classes">Exception Classes</a>
</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<p style="padding-left: 30px;">&lt;all methods inherited from <a href="#class_builtins_Exception">builtins.Exception</a>&gt;</p>
<hr>
<h2><strong><a class="offsanchor" name="class_ba_OldWindow">ba.OldWindow</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">Temp for transitioning windows over to UILocationWindows.</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_OldWindow____init__">&lt;constructor&gt;</a>, <a href="#method_ba_OldWindow__get_root_widget">get_root_widget()</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_OldWindow____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.OldWindow(root_widget: <a href="#class_ba_Widget">ba.Widget</a>)</span></p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_OldWindow__get_root_widget"><strong>get_root_widget()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_root_widget(self) -&gt; <a href="#class_ba_Widget">ba.Widget</a></span></p>

<p style="padding-left: 60px;">Return the root widget.</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_OutOfBoundsMessage">ba.OutOfBoundsMessage</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">A message telling an object that it is out of bounds.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Message_Classes">Message Classes</a>
</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_OutOfBoundsMessage____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.OutOfBoundsMessage()</span></p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_Permission">ba.Permission</a></strong></h3>
<p style="padding-left: 30px;">inherits from: enum.Enum</p>
<p style="padding-left: 30px;">Permissions that can be requested from the OS.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Enums">Enums</a>
</p>

<h3 style="padding-left: 0px;">Values:</h3>
<ul>
<li>STORAGE</li>
</ul>
<hr>
<h2><strong><a class="offsanchor" name="class_ba_PickedUpMessage">ba.PickedUpMessage</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">Tells an object that it has been picked up by something.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Message_Classes">Message Classes</a></p>

<h3 style="padding-left: 0px;">Attributes:</h3>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_PickedUpMessage__node"><strong>node</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"><a href="#class_ba_Node">ba.Node</a></span></p>
<p style="padding-left: 60px;">The <a href="#class_ba_Node">ba.Node</a> doing the picking up.</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_PickedUpMessage____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.PickedUpMessage(node: <a href="#class_ba_Node">ba.Node</a>)</span></p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_PickUpMessage">ba.PickUpMessage</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">Tells an object that it has picked something up.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Message_Classes">Message Classes</a></p>

<h3 style="padding-left: 0px;">Attributes:</h3>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_PickUpMessage__node"><strong>node</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"><a href="#class_ba_Node">ba.Node</a></span></p>
<p style="padding-left: 60px;">The <a href="#class_ba_Node">ba.Node</a> that is getting picked up.</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_PickUpMessage____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.PickUpMessage(node: <a href="#class_ba_Node">ba.Node</a>)</span></p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_Player">ba.Player</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">A reference to a player in the game.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a></p>

<p style="padding-left: 30px;">These are created and managed internally and
provided to your Session/Activity instances.
Be aware that, like <a href="#class_ba_Node">ba.Nodes</a>, <a href="#class_ba_Player">ba.Player</a> objects are 'weak'
references under-the-hood; a player can leave the game at
 any point. For this reason, you should make judicious use of the
<a href="#attr_ba_Player__exists">ba.Player.exists</a> attribute (or boolean operator) to ensure that a
Player is still present if retaining references to one for any
length of time.</p>

<h3 style="padding-left: 0px;">Attributes:</h3>
<h5 style="padding-left: 30px;"><a href="#attr_ba_Player__actor">actor</a>, <a href="#attr_ba_Player__character">character</a>, <a href="#attr_ba_Player__color">color</a>, <a href="#attr_ba_Player__exists">exists</a>, <a href="#attr_ba_Player__gamedata">gamedata</a>, <a href="#attr_ba_Player__highlight">highlight</a>, <a href="#attr_ba_Player__in_game">in_game</a>, <a href="#attr_ba_Player__node">node</a>, <a href="#attr_ba_Player__sessiondata">sessiondata</a>, <a href="#attr_ba_Player__team">team</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Player__actor"><strong>actor</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"> Optional[<a href="#class_ba_Actor">ba.Actor</a>]</span></p>
<p style="padding-left: 60px;">The current <a href="#class_ba_Actor">ba.Actor</a> associated with this Player.
This may be None</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Player__character"><strong>character</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"> str</span></p>
<p style="padding-left: 60px;">The character this player has selected in their profile.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Player__color"><strong>color</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"> Sequence[float]</span></p>
<p style="padding-left: 60px;">The base color for this Player.
In team games this will match the <a href="#class_ba_Team">ba.Team</a>'s color.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Player__exists"><strong>exists</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"> bool</span></p>
<p style="padding-left: 60px;">Whether the player still exists.
Most functionality will fail on a nonexistent player.</p>

<p style="padding-left: 60px;">Note that you can also use the boolean operator for this same
functionality, so a statement such as "if player" will do
the right thing both for Player objects and values of None.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Player__gamedata"><strong>gamedata</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"> Dict</span></p>
<p style="padding-left: 60px;">A dict for use by the current <a href="#class_ba_Activity">ba.Activity</a> for
storing data associated with this Player.
This gets cleared for each new <a href="#class_ba_Activity">ba.Activity</a>.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Player__highlight"><strong>highlight</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"> Sequence[float]</span></p>
<p style="padding-left: 60px;">A secondary color for this player.
This is used for minor highlights and accents
to allow a player to stand apart from his teammates
who may all share the same team (primary) color.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Player__in_game"><strong>in_game</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"> bool</span></p>
<p style="padding-left: 60px;">This bool value will be True once the Player has completed
any lobby character/team selection.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Player__node"><strong>node</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"> Optional[<a href="#class_ba_Node">ba.Node</a>]</span></p>
<p style="padding-left: 60px;">A <a href="#class_ba_Node">ba.Node</a> of type 'player' associated with this Player.
This Node exists in the currently active game and can be used
to get a generic player position/etc.
This will be None if the Player is not in a game.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Player__sessiondata"><strong>sessiondata</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"> Dict</span></p>
<p style="padding-left: 60px;">A dict for use by the current <a href="#class_ba_Session">ba.Session</a> for
storing data associated with this player.
This persists for the duration of the session.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Player__team"><strong>team</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"> <a href="#class_ba_Team">ba.Team</a></span></p>
<p style="padding-left: 60px;">The <a href="#class_ba_Team">ba.Team</a> this Player is on.  If the Player is
still in its lobby selecting a team/etc. then a
<a href="#class_ba_TeamNotFoundError">ba.TeamNotFoundError</a> will be raised.</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_Player__assign_input_call">assign_input_call()</a>, <a href="#method_ba_Player__get_account_id">get_account_id()</a>, <a href="#method_ba_Player__get_icon">get_icon()</a>, <a href="#method_ba_Player__get_id">get_id()</a>, <a href="#method_ba_Player__get_input_device">get_input_device()</a>, <a href="#method_ba_Player__get_name">get_name()</a>, <a href="#method_ba_Player__is_alive">is_alive()</a>, <a href="#method_ba_Player__remove_from_game">remove_from_game()</a>, <a href="#method_ba_Player__reset_input">reset_input()</a>, <a href="#method_ba_Player__set_actor">set_actor()</a>, <a href="#method_ba_Player__set_name">set_name()</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Player__assign_input_call"><strong>assign_input_call()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">assign_input_call(type: Union[str, Tuple[str, ...]],
  call: Callable) -&gt; None</span></p>

<p style="padding-left: 60px;">Set the python callable to be run for one or more types of input.
Valid type values are: 'jumpPress', 'jumpRelease', 'punchPress',
  'punchRelease','bombPress', 'bombRelease', 'pickUpPress',
  'pickUpRelease', 'upDown','leftRight','upPress', 'upRelease',
  'downPress', 'downRelease', 'leftPress','leftRelease','rightPress',
  'rightRelease', 'run', 'flyPress', 'flyRelease', 'startPress',
  'startRelease'</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Player__get_account_id"><strong>get_account_id()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_account_id() -&gt; str</span></p>

<p style="padding-left: 60px;">Return the Account ID this player is signed in under, if
there is one and it can be determined with relative certainty.
Returns None otherwise. Note that this may require an active
internet connection (especially for network-connected players)
and may return None for a short while after a player initially
joins (while verification occurs).</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Player__get_icon"><strong>get_icon()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_icon() -&gt; Dict[str, Any]</span></p>

<p style="padding-left: 60px;">Returns the character's icon (images, colors, etc contained in a dict)</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Player__get_id"><strong>get_id()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_id() -&gt; int</span></p>

<p style="padding-left: 60px;">Returns the unique numeric player ID for this player.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Player__get_input_device"><strong>get_input_device()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_input_device() -&gt; <a href="#class_ba_InputDevice">ba.InputDevice</a></span></p>

<p style="padding-left: 60px;">Returns the player's input device.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Player__get_name"><strong>get_name()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_name(full: bool = False, icon: bool = True) -&gt; str</span></p>

<p style="padding-left: 60px;">Returns the player's name. If icon is True, the long version of the
name may include an icon.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Player__is_alive"><strong>is_alive()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">is_alive() -&gt; bool</span></p>

<p style="padding-left: 60px;">Returns True if the player has a <a href="#class_ba_Actor">ba.Actor</a> assigned and its
is_alive() method return True. False is returned otherwise.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Player__remove_from_game"><strong>remove_from_game()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">remove_from_game() -&gt; None</span></p>

<p style="padding-left: 60px;">Removes the player from the game.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Player__reset_input"><strong>reset_input()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">reset_input() -&gt; None</span></p>

<p style="padding-left: 60px;">Clears out the player's assigned input actions.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Player__set_actor"><strong>set_actor()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">set_actor(actor: Optional[<a href="#class_ba_Actor">ba.Actor</a>]) -&gt; None</span></p>

<p style="padding-left: 60px;">Set the player's associated <a href="#class_ba_Actor">ba.Actor</a>.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Player__set_name"><strong>set_name()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">set_name(name: str, full_name: str = None, real: bool = True)
  -&gt; None</span></p>

<p style="padding-left: 60px;">Set the player's name to the provided string.
A number will automatically be appended if the name is not unique from
other players.</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_PlayerNotFoundError">ba.PlayerNotFoundError</a></strong></h3>
<p style="padding-left: 30px;">inherits from: <a href="#class_ba_NotFoundError">ba.NotFoundError</a>, Exception, BaseException</p>
<p style="padding-left: 30px;">Exception raised when an expected <a href="#class_ba_Player">ba.Player</a> does not exist.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Exception_Classes">Exception Classes</a>
</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<p style="padding-left: 30px;">&lt;all methods inherited from <a href="#class_ba_NotFoundError">ba.NotFoundError</a>&gt;</p>
<hr>
<h2><strong><a class="offsanchor" name="class_ba_PlayerRecord">ba.PlayerRecord</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">Stats for an individual player in a <a href="#class_ba_Stats">ba.Stats</a> object.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a></p>

<p style="padding-left: 30px;">    This does not necessarily correspond to a <a href="#class_ba_Player">ba.Player</a> that is
    still present (stats may be retained for players that leave
    mid-game)
</p>

<h3 style="padding-left: 0px;">Attributes:</h3>
<h5 style="padding-left: 30px;"><a href="#attr_ba_PlayerRecord__player">player</a>, <a href="#attr_ba_PlayerRecord__team">team</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_PlayerRecord__player"><strong>player</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"><a href="#class_ba_Player">ba.Player</a></span></p>
<p style="padding-left: 60px;">Return the instance's associated <a href="#class_ba_Player">ba.Player</a>.</p>

<p style="padding-left: 60px;">        Raises a <a href="#class_ba_PlayerNotFoundError">ba.PlayerNotFoundError</a> if the player no longer exists.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_PlayerRecord__team"><strong>team</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"><a href="#class_ba_Team">ba.Team</a></span></p>
<p style="padding-left: 60px;">The <a href="#class_ba_Team">ba.Team</a> the last associated player was last on.</p>

<p style="padding-left: 60px;">        This can still return a valid result even if the player is gone.
        Raises a <a href="#class_ba_TeamNotFoundError">ba.TeamNotFoundError</a> if the team no longer exists.</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_PlayerRecord____init__">&lt;constructor&gt;</a>, <a href="#method_ba_PlayerRecord__associate_with_player">associate_with_player()</a>, <a href="#method_ba_PlayerRecord__cancel_multi_kill_timer">cancel_multi_kill_timer()</a>, <a href="#method_ba_PlayerRecord__get_icon">get_icon()</a>, <a href="#method_ba_PlayerRecord__get_last_player">get_last_player()</a>, <a href="#method_ba_PlayerRecord__get_name">get_name()</a>, <a href="#method_ba_PlayerRecord__get_spaz">get_spaz()</a>, <a href="#method_ba_PlayerRecord__getactivity">getactivity()</a>, <a href="#method_ba_PlayerRecord__submit_kill">submit_kill()</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_PlayerRecord____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.PlayerRecord(name: str, name_full: str, player: <a href="#class_ba_Player">ba.Player</a>, stats: <a href="#class_ba_Stats">ba.Stats</a>)</span></p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_PlayerRecord__associate_with_player"><strong>associate_with_player()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">associate_with_player(self, player: <a href="#class_ba_Player">ba.Player</a>) -&gt; None</span></p>

<p style="padding-left: 60px;">Associate this entry with a <a href="#class_ba_Player">ba.Player</a>.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_PlayerRecord__cancel_multi_kill_timer"><strong>cancel_multi_kill_timer()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">cancel_multi_kill_timer(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Cancel any multi-kill timer for this player entry.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_PlayerRecord__get_icon"><strong>get_icon()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_icon(self) -&gt; Dict[str, Any]</span></p>

<p style="padding-left: 60px;">Get the icon for this instance's player.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_PlayerRecord__get_last_player"><strong>get_last_player()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_last_player(self) -&gt; <a href="#class_ba_Player">ba.Player</a></span></p>

<p style="padding-left: 60px;">Return the last <a href="#class_ba_Player">ba.Player</a> we were associated with.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_PlayerRecord__get_name"><strong>get_name()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_name(self, full: bool = False) -&gt; str</span></p>

<p style="padding-left: 60px;">Return the player entry's name.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_PlayerRecord__get_spaz"><strong>get_spaz()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_spaz(self) -&gt; Optional[<a href="#class_ba_Actor">ba.Actor</a>]</span></p>

<p style="padding-left: 60px;">Return the player entry's spaz.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_PlayerRecord__getactivity"><strong>getactivity()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">getactivity(self) -&gt; Optional[<a href="#class_ba_Activity">ba.Activity</a>]</span></p>

<p style="padding-left: 60px;">Return the <a href="#class_ba_Activity">ba.Activity</a> this instance is currently associated with.</p>

<p style="padding-left: 60px;">Returns None if the activity no longer exists.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_PlayerRecord__submit_kill"><strong>submit_kill()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">submit_kill(self, showpoints: bool = True) -&gt; None</span></p>

<p style="padding-left: 60px;">Submit a kill for this player entry.</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_PlayerScoredMessage">ba.PlayerScoredMessage</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">Informs something that a <a href="#class_ba_Player">ba.Player</a> scored.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Message_Classes">Message Classes</a></p>

<h3 style="padding-left: 0px;">Attributes:</h3>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_PlayerScoredMessage__score"><strong>score</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">int</span></p>
<p style="padding-left: 60px;">The score value.</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_PlayerScoredMessage____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.PlayerScoredMessage(score: int)</span></p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_PowerupAcceptMessage">ba.PowerupAcceptMessage</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">A message informing a ba.Powerup that it was accepted.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Message_Classes">Message Classes</a></p>

<p style="padding-left: 30px;">    This is generally sent in response to a <a href="#class_ba_PowerupMessage">ba.PowerupMessage</a>
    to inform the box (or whoever granted it) that it can go away.
</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_PowerupAcceptMessage____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.PowerupAcceptMessage()</span></p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_PowerupMessage">ba.PowerupMessage</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">A message telling an object to accept a powerup.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Message_Classes">Message Classes</a></p>

<p style="padding-left: 30px;">    This message is normally received by touching a ba.PowerupBox.</p>

<h3 style="padding-left: 0px;">Attributes:</h3>
<h5 style="padding-left: 30px;"><a href="#attr_ba_PowerupMessage__poweruptype">poweruptype</a>, <a href="#attr_ba_PowerupMessage__source_node">source_node</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_PowerupMessage__poweruptype"><strong>poweruptype</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">str</span></p>
<p style="padding-left: 60px;">The type of powerup to be granted (a string).
See ba.Powerup.poweruptype for available type values.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_PowerupMessage__source_node"><strong>source_node</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">Optional[<a href="#class_ba_Node">ba.Node</a>]</span></p>
<p style="padding-left: 60px;">The node the powerup game from, or None otherwise.
If a powerup is accepted, a <a href="#class_ba_PowerupAcceptMessage">ba.PowerupAcceptMessage</a> should be sent
back to the source_node to inform it of the fact. This will generally
cause the powerup box to make a sound and disappear or whatnot.</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_PowerupMessage____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.PowerupMessage(poweruptype: str, source_node: Optional[<a href="#class_ba_Node">ba.Node</a>] = None)</span></p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_Session">ba.Session</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">Defines a high level series of activities with a common purpose.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a></p>

<p style="padding-left: 30px;">    Examples of sessions are <a href="#class_ba_FreeForAllSession">ba.FreeForAllSession</a>, <a href="#class_ba_TeamsSession">ba.TeamsSession</a>, and
    <a href="#class_ba_CoopSession">ba.CoopSession</a>.</p>

<p style="padding-left: 30px;">    A Session is responsible for wrangling and transitioning between various
    <a href="#class_ba_Activity">ba.Activity</a> instances such as mini-games and score-screens, and for
    maintaining state between them (players, teams, score tallies, etc).</p>

<h3 style="padding-left: 0px;">Attributes:</h3>
<h5 style="padding-left: 30px;"><a href="#attr_ba_Session__campaign">campaign</a>, <a href="#attr_ba_Session__lobby">lobby</a>, <a href="#attr_ba_Session__max_players">max_players</a>, <a href="#attr_ba_Session__min_players">min_players</a>, <a href="#attr_ba_Session__players">players</a>, <a href="#attr_ba_Session__teams">teams</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Session__campaign"><strong>campaign</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">Optional[<a href="#class_ba_Campaign">ba.Campaign</a>]</span></p>
<p style="padding-left: 60px;">The <a href="#class_ba_Campaign">ba.Campaign</a> instance this Session represents, or None if
there is no associated Campaign.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Session__lobby"><strong>lobby</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"><a href="#class_ba_Lobby">ba.Lobby</a></span></p>
<p style="padding-left: 60px;">The <a href="#class_ba_Lobby">ba.Lobby</a> instance where new <a href="#class_ba_Player">ba.Players</a> go to select a
Profile/Team/etc. before being added to games.
Be aware this value may be None if a Session does not allow
any such selection.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Session__max_players"><strong>max_players</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">int</span></p>
<p style="padding-left: 60px;">The maximum number of Players allowed in the Session.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Session__min_players"><strong>min_players</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">int</span></p>
<p style="padding-left: 60px;">The minimum number of Players who must be present for the Session
to proceed past the initial joining screen.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Session__players"><strong>players</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">List[<a href="#class_ba_Player">ba.Player</a>]</span></p>
<p style="padding-left: 60px;">All <a href="#class_ba_Player">ba.Players</a> in the Session. Most things should use the player
list in <a href="#class_ba_Activity">ba.Activity</a>; not this. Some players, such as those who have
not yet selected a character, will only appear on this list.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Session__teams"><strong>teams</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">List[<a href="#class_ba_Team">ba.Team</a>]</span></p>
<p style="padding-left: 60px;">All the <a href="#class_ba_Team">ba.Teams</a> in the Session. Most things should use the team
list in <a href="#class_ba_Activity">ba.Activity</a>; not this.</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_Session____init__">&lt;constructor&gt;</a>, <a href="#method_ba_Session__begin_next_activity">begin_next_activity()</a>, <a href="#method_ba_Session__end">end()</a>, <a href="#method_ba_Session__end_activity">end_activity()</a>, <a href="#method_ba_Session__get_custom_menu_entries">get_custom_menu_entries()</a>, <a href="#method_ba_Session__getactivity">getactivity()</a>, <a href="#method_ba_Session__handlemessage">handlemessage()</a>, <a href="#method_ba_Session__on_activity_end">on_activity_end()</a>, <a href="#method_ba_Session__on_player_leave">on_player_leave()</a>, <a href="#method_ba_Session__on_player_request">on_player_request()</a>, <a href="#method_ba_Session__on_team_join">on_team_join()</a>, <a href="#method_ba_Session__on_team_leave">on_team_leave()</a>, <a href="#method_ba_Session__set_activity">set_activity()</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Session____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.Session(depsets: Sequence[<a href="#class_ba_DependencySet">ba.DependencySet</a>], team_names: Sequence[str] = None, team_colors: Sequence[Sequence[float]] = None, use_team_colors: bool = True, min_players: int = 1, max_players: int = 8, allow_mid_activity_joins: bool = True)</span></p>

<p style="padding-left: 60px;">Instantiate a session.</p>

<p style="padding-left: 60px;">depsets should be a sequence of successfully resolved <a href="#class_ba_DependencySet">ba.DependencySet</a>
instances; one for each <a href="#class_ba_Activity">ba.Activity</a> the session may potentially run.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Session__begin_next_activity"><strong>begin_next_activity()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">begin_next_activity(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Called once the previous activity has been totally torn down.</p>

<p style="padding-left: 60px;">This means we're ready to begin the next one</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Session__end"><strong>end()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">end(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Initiates an end to the session and a return to the main menu.</p>

<p style="padding-left: 60px;">Note that this happens asynchronously, allowing the
session and its activities to shut down gracefully.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Session__end_activity"><strong>end_activity()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">end_activity(self, activity: <a href="#class_ba_Activity">ba.Activity</a>, results: Any, delay: float, force: bool) -&gt; None</span></p>

<p style="padding-left: 60px;">Commence shutdown of a <a href="#class_ba_Activity">ba.Activity</a> (if not already occurring).</p>

<p style="padding-left: 60px;">'delay' is the time delay before the Activity actually ends
(in seconds). Further calls to end() will be ignored up until
this time, unless 'force' is True, in which case the new results
will replace the old.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Session__get_custom_menu_entries"><strong>get_custom_menu_entries()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_custom_menu_entries(self) -&gt; List[Dict[str, Any]]</span></p>

<p style="padding-left: 60px;">Subclasses can override this to provide custom menu entries.</p>

<p style="padding-left: 60px;">The returned value should be a list of dicts, each containing
a 'label' and 'call' entry, with 'label' being the text for
the entry and 'call' being the callable to trigger if the entry
is pressed.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Session__getactivity"><strong>getactivity()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">getactivity(self) -&gt; Optional[<a href="#class_ba_Activity">ba.Activity</a>]</span></p>

<p style="padding-left: 60px;">Return the current foreground activity for this session.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Session__handlemessage"><strong>handlemessage()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">handlemessage(self, msg: Any) -&gt; Any</span></p>

<p style="padding-left: 60px;">General message handling; can be passed any <a href="#class_category_Message_Classes">message object</a>.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Session__on_activity_end"><strong>on_activity_end()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">on_activity_end(self, activity: <a href="#class_ba_Activity">ba.Activity</a>, results: Any) -&gt; None</span></p>

<p style="padding-left: 60px;">Called when the current <a href="#class_ba_Activity">ba.Activity</a> has ended.</p>

<p style="padding-left: 60px;">The <a href="#class_ba_Session">ba.Session</a> should look at the results and start
another <a href="#class_ba_Activity">ba.Activity</a>.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Session__on_player_leave"><strong>on_player_leave()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">on_player_leave(self, player: <a href="#class_ba_Player">ba.Player</a>) -&gt; None</span></p>

<p style="padding-left: 60px;">Called when a previously-accepted <a href="#class_ba_Player">ba.Player</a> leaves the session.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Session__on_player_request"><strong>on_player_request()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">on_player_request(self, player: <a href="#class_ba_Player">ba.Player</a>) -&gt; bool</span></p>

<p style="padding-left: 60px;">Called when a new <a href="#class_ba_Player">ba.Player</a> wants to join the Session.</p>

<p style="padding-left: 60px;">This should return True or False to accept/reject.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Session__on_team_join"><strong>on_team_join()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">on_team_join(self, team: <a href="#class_ba_Team">ba.Team</a>) -&gt; None</span></p>

<p style="padding-left: 60px;">Called when a new <a href="#class_ba_Team">ba.Team</a> joins the session.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Session__on_team_leave"><strong>on_team_leave()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">on_team_leave(self, team: <a href="#class_ba_Team">ba.Team</a>) -&gt; None</span></p>

<p style="padding-left: 60px;">Called when a <a href="#class_ba_Team">ba.Team</a> is leaving the session.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Session__set_activity"><strong>set_activity()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">set_activity(self, activity: <a href="#class_ba_Activity">ba.Activity</a>) -&gt; None</span></p>

<p style="padding-left: 60px;">Assign a new current <a href="#class_ba_Activity">ba.Activity</a> for the session.</p>

<p style="padding-left: 60px;">Note that this will not change the current context to the new
Activity's. Code must be run in the new activity's methods
(on_transition_in, etc) to get it. (so you can't do
session.set_activity(foo) and then <a href="#function_ba_newnode">ba.newnode</a>() to add a node to foo)</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_SessionNotFoundError">ba.SessionNotFoundError</a></strong></h3>
<p style="padding-left: 30px;">inherits from: <a href="#class_ba_NotFoundError">ba.NotFoundError</a>, Exception, BaseException</p>
<p style="padding-left: 30px;">Exception raised when an expected <a href="#class_ba_Session">ba.Session</a> does not exist.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Exception_Classes">Exception Classes</a>
</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<p style="padding-left: 30px;">&lt;all methods inherited from <a href="#class_ba_NotFoundError">ba.NotFoundError</a>&gt;</p>
<hr>
<h2><strong><a class="offsanchor" name="class_ba_ShouldShatterMessage">ba.ShouldShatterMessage</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">Tells an object that it should shatter.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Message_Classes">Message Classes</a>
</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_ShouldShatterMessage____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.ShouldShatterMessage()</span></p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_Sound">ba.Sound</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">A reference to a sound.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Asset_Classes">Asset Classes</a></p>

<p style="padding-left: 30px;">Use <a href="#function_ba_getsound">ba.getsound</a>() to instantiate one.</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_SpecialChar">ba.SpecialChar</a></strong></h3>
<p style="padding-left: 30px;">inherits from: enum.Enum</p>
<p style="padding-left: 30px;">Special characters the game can print.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Enums">Enums</a>
</p>

<h3 style="padding-left: 0px;">Values:</h3>
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
<h2><strong><a class="offsanchor" name="class_ba_StandMessage">ba.StandMessage</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">A message telling an object to move to a position in space.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Message_Classes">Message Classes</a></p>

<p style="padding-left: 30px;">    Used when teleporting players to home base, etc.</p>

<h3 style="padding-left: 0px;">Attributes:</h3>
<h5 style="padding-left: 30px;"><a href="#attr_ba_StandMessage__angle">angle</a>, <a href="#attr_ba_StandMessage__position">position</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_StandMessage__angle"><strong>angle</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">float</span></p>
<p style="padding-left: 60px;">The angle to face (in degrees)</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_StandMessage__position"><strong>position</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">Sequence[float]</span></p>
<p style="padding-left: 60px;">Where to move to.</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_StandMessage____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.StandMessage(position: Sequence[float] = (0.0, 0.0, 0.0), angle: float = 0.0)</span></p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_Stats">ba.Stats</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">Manages scores and statistics for a <a href="#class_ba_Session">ba.Session</a>.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a>
</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_Stats____init__">&lt;constructor&gt;</a>, <a href="#method_ba_Stats__get_records">get_records()</a>, <a href="#method_ba_Stats__getactivity">getactivity()</a>, <a href="#method_ba_Stats__player_got_hit">player_got_hit()</a>, <a href="#method_ba_Stats__player_got_new_spaz">player_got_new_spaz()</a>, <a href="#method_ba_Stats__player_lost_spaz">player_lost_spaz()</a>, <a href="#method_ba_Stats__player_scored">player_scored()</a>, <a href="#method_ba_Stats__register_player">register_player()</a>, <a href="#method_ba_Stats__reset">reset()</a>, <a href="#method_ba_Stats__reset_accum">reset_accum()</a>, <a href="#method_ba_Stats__set_activity">set_activity()</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Stats____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.Stats()</span></p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Stats__get_records"><strong>get_records()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_records(self) -&gt; Dict[str, <a href="#class_ba_PlayerRecord">ba.PlayerRecord</a>]</span></p>

<p style="padding-left: 60px;">Get PlayerRecord corresponding to still-existing players.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Stats__getactivity"><strong>getactivity()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">getactivity(self) -&gt; Optional[<a href="#class_ba_Activity">ba.Activity</a>]</span></p>

<p style="padding-left: 60px;">Get the activity associated with this instance.</p>

<p style="padding-left: 60px;">May return None.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Stats__player_got_hit"><strong>player_got_hit()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">player_got_hit(self, player: <a href="#class_ba_Player">ba.Player</a>) -&gt; None</span></p>

<p style="padding-left: 60px;">Call this when a player got hit.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Stats__player_got_new_spaz"><strong>player_got_new_spaz()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">player_got_new_spaz(self, player: <a href="#class_ba_Player">ba.Player</a>, spaz: <a href="#class_ba_Actor">ba.Actor</a>) -&gt; None</span></p>

<p style="padding-left: 60px;">Call this when a player gets a new Spaz.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Stats__player_lost_spaz"><strong>player_lost_spaz()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">player_lost_spaz(self, player: <a href="#class_ba_Player">ba.Player</a>, killed: bool = False, killer: <a href="#class_ba_Player">ba.Player</a> = None) -&gt; None</span></p>

<p style="padding-left: 60px;">Should be called when a player loses a spaz.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Stats__player_scored"><strong>player_scored()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">player_scored(self, player: <a href="#class_ba_Player">ba.Player</a>, base_points: int = 1, target: Sequence[float] = None, kill: bool = False, victim_player: <a href="#class_ba_Player">ba.Player</a> = None, scale: float = 1.0, color: Sequence[float] = None, title: Union[str, <a href="#class_ba_Lstr">ba.Lstr</a>] = None, screenmessage: bool = True, display: bool = True, importance: int = 1, showpoints: bool = True, big_message: bool = False) -&gt; int</span></p>

<p style="padding-left: 60px;">Register a score for the player.</p>

<p style="padding-left: 60px;">Return value is actual score with multipliers and such factored in.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Stats__register_player"><strong>register_player()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">register_player(self, player: <a href="#class_ba_Player">ba.Player</a>) -&gt; None</span></p>

<p style="padding-left: 60px;">Register a player with this score-set.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Stats__reset"><strong>reset()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">reset(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Reset the stats instance completely.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Stats__reset_accum"><strong>reset_accum()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">reset_accum(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Reset per-sound sub-scores.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Stats__set_activity"><strong>set_activity()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">set_activity(self, activity: <a href="#class_ba_Activity">ba.Activity</a>) -&gt; None</span></p>

<p style="padding-left: 60px;">Set the current activity for this instance.</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_Team">ba.Team</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">A team of one or more <a href="#class_ba_Player">ba.Players</a>.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a></p>

<p style="padding-left: 30px;">    Note that a player *always* has a team;
    in some cases, such as free-for-all <a href="#class_ba_Session">ba.Sessions</a>,
    each team consists of just one <a href="#class_ba_Player">ba.Player</a>.</p>

<h3 style="padding-left: 0px;">Attributes:</h3>
<h5 style="padding-left: 30px;"><a href="#attr_ba_Team__color">color</a>, <a href="#attr_ba_Team__gamedata">gamedata</a>, <a href="#attr_ba_Team__name">name</a>, <a href="#attr_ba_Team__players">players</a>, <a href="#attr_ba_Team__sessiondata">sessiondata</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Team__color"><strong>color</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">Tuple[float, ...]</span></p>
<p style="padding-left: 60px;">The team's color.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Team__gamedata"><strong>gamedata</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">Dict</span></p>
<p style="padding-left: 60px;">A dict for use by the current <a href="#class_ba_Activity">ba.Activity</a>
for storing data associated with this team.
This gets cleared for each new <a href="#class_ba_Activity">ba.Activity</a>.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Team__name"><strong>name</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">Union[<a href="#class_ba_Lstr">ba.Lstr</a>, str]</span></p>
<p style="padding-left: 60px;">The team's name.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Team__players"><strong>players</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">List[<a href="#class_ba_Player">ba.Player</a>]</span></p>
<p style="padding-left: 60px;">The list of <a href="#class_ba_Player">ba.Players</a> on the team.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Team__sessiondata"><strong>sessiondata</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;">Dict</span></p>
<p style="padding-left: 60px;">A dict for use by the current <a href="#class_ba_Session">ba.Session</a> for
storing data associated with this team.
Unlike gamedata, this persists for the duration
of the session.</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_Team____init__">&lt;constructor&gt;</a>, <a href="#method_ba_Team__celebrate">celebrate()</a>, <a href="#method_ba_Team__get_id">get_id()</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Team____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.Team(team_id: 'int' = 0, name: 'Union[<a href="#class_ba_Lstr">ba.Lstr</a>, str]' = '', color: 'Sequence[float]' = (1.0, 1.0, 1.0))</span></p>

<p style="padding-left: 60px;">Instantiate a ba.Team.</p>

<p style="padding-left: 60px;">In most cases, all teams are provided to you by the <a href="#class_ba_Session">ba.Session</a>,
<a href="#class_ba_Session">ba.Session</a>, so calling this shouldn't be necessary.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Team__celebrate"><strong>celebrate()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">celebrate(self, duration: float = 10.0) -&gt; None</span></p>

<p style="padding-left: 60px;">Tells all players on the team to celebrate.</p>

<p style="padding-left: 60px;">duration is given in seconds.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Team__get_id"><strong>get_id()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_id(self) -&gt; int</span></p>

<p style="padding-left: 60px;">Returns the numeric team ID.</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_TeamBaseSession">ba.TeamBaseSession</a></strong></h3>
<p style="padding-left: 30px;">inherits from: <a href="#class_ba_Session">ba.Session</a></p>
<p style="padding-left: 30px;">Common base class for <a href="#class_ba_TeamsSession">ba.TeamsSession</a> and <a href="#class_ba_FreeForAllSession">ba.FreeForAllSession</a>.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a></p>

<p style="padding-left: 30px;">    Free-for-all-mode is essentially just teams-mode with each <a href="#class_ba_Player">ba.Player</a> having
    their own <a href="#class_ba_Team">ba.Team</a>, so there is much overlap in functionality.
</p>

<h3 style="padding-left: 0px;">Attributes Inherited:</h3>
<h5 style="padding-left: 30px;"><a href="#attr_ba_Session__campaign">campaign</a>, <a href="#attr_ba_Session__lobby">lobby</a>, <a href="#attr_ba_Session__max_players">max_players</a>, <a href="#attr_ba_Session__min_players">min_players</a>, <a href="#attr_ba_Session__players">players</a>, <a href="#attr_ba_Session__teams">teams</a></h5>
<h3 style="padding-left: 0px;">Methods Inherited:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_Session__begin_next_activity">begin_next_activity()</a>, <a href="#method_ba_Session__end">end()</a>, <a href="#method_ba_Session__end_activity">end_activity()</a>, <a href="#method_ba_Session__get_custom_menu_entries">get_custom_menu_entries()</a>, <a href="#method_ba_Session__getactivity">getactivity()</a>, <a href="#method_ba_Session__handlemessage">handlemessage()</a>, <a href="#method_ba_Session__launch_end_session_activity">launch_end_session_activity()</a>, <a href="#method_ba_Session__on_player_leave">on_player_leave()</a>, <a href="#method_ba_Session__on_player_request">on_player_request()</a>, <a href="#method_ba_Session__on_team_leave">on_team_leave()</a>, <a href="#method_ba_Session__set_activity">set_activity()</a></h5>
<h3 style="padding-left: 0px;">Methods Defined or Overridden:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_TeamBaseSession____init__">&lt;constructor&gt;</a>, <a href="#method_ba_TeamBaseSession__announce_game_results">announce_game_results()</a>, <a href="#method_ba_TeamBaseSession__get_ffa_series_length">get_ffa_series_length()</a>, <a href="#method_ba_TeamBaseSession__get_game_number">get_game_number()</a>, <a href="#method_ba_TeamBaseSession__get_max_players">get_max_players()</a>, <a href="#method_ba_TeamBaseSession__get_next_game_description">get_next_game_description()</a>, <a href="#method_ba_TeamBaseSession__get_series_length">get_series_length()</a>, <a href="#method_ba_TeamBaseSession__on_activity_end">on_activity_end()</a>, <a href="#method_ba_TeamBaseSession__on_team_join">on_team_join()</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_TeamBaseSession____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.TeamBaseSession()</span></p>

<p style="padding-left: 60px;">Set up playlists and launches a <a href="#class_ba_Activity">ba.Activity</a> to accept joiners.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_TeamBaseSession__announce_game_results"><strong>announce_game_results()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">announce_game_results(self, activity: <a href="#class_ba_GameActivity">ba.GameActivity</a>, results: <a href="#class_ba_TeamGameResults">ba.TeamGameResults</a>, delay: float, announce_winning_team: bool = True) -&gt; None</span></p>

<p style="padding-left: 60px;">Show basic game result at the end of a game.</p>

<p style="padding-left: 60px;">(before transitioning to a score screen).
This will include a zoom-text of 'BLUE WINS'
or whatnot, along with a possible audio
announcement of the same.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_TeamBaseSession__get_ffa_series_length"><strong>get_ffa_series_length()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_ffa_series_length(self) -&gt; int</span></p>

<p style="padding-left: 60px;">Return free-for-all series length.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_TeamBaseSession__get_game_number"><strong>get_game_number()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_game_number(self) -&gt; int</span></p>

<p style="padding-left: 60px;">Returns which game in the series is currently being played.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_TeamBaseSession__get_max_players"><strong>get_max_players()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_max_players(self) -&gt; int</span></p>

<p style="padding-left: 60px;">Return max number of <a href="#class_ba_Player">ba.Players</a> allowed to join the game at once.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_TeamBaseSession__get_next_game_description"><strong>get_next_game_description()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_next_game_description(self) -&gt; <a href="#class_ba_Lstr">ba.Lstr</a></span></p>

<p style="padding-left: 60px;">Returns a description of the next game on deck.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_TeamBaseSession__get_series_length"><strong>get_series_length()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_series_length(self) -&gt; int</span></p>

<p style="padding-left: 60px;">Return teams series length.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_TeamBaseSession__on_activity_end"><strong>on_activity_end()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">on_activity_end(self, activity: <a href="#class_ba_Activity">ba.Activity</a>, results: Any) -&gt; None</span></p>

<p style="padding-left: 60px;">Called when the current <a href="#class_ba_Activity">ba.Activity</a> has ended.</p>

<p style="padding-left: 60px;">The <a href="#class_ba_Session">ba.Session</a> should look at the results and start
another <a href="#class_ba_Activity">ba.Activity</a>.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_TeamBaseSession__on_team_join"><strong>on_team_join()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">on_team_join(self, team: <a href="#class_ba_Team">ba.Team</a>) -&gt; None</span></p>

<p style="padding-left: 60px;">Called when a new <a href="#class_ba_Team">ba.Team</a> joins the session.</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_TeamGameActivity">ba.TeamGameActivity</a></strong></h3>
<p style="padding-left: 30px;">inherits from: <a href="#class_ba_GameActivity">ba.GameActivity</a>, <a href="#class_ba_Activity">ba.Activity</a>, <a href="#class_ba_DependencyComponent">ba.DependencyComponent</a></p>
<p style="padding-left: 30px;">Base class for teams and free-for-all mode games.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a></p>

<p style="padding-left: 30px;">    (Free-for-all is essentially just a special case where every
    <a href="#class_ba_Player">ba.Player</a> has their own <a href="#class_ba_Team">ba.Team</a>)
</p>

<h3 style="padding-left: 0px;">Attributes Inherited:</h3>
<h5 style="padding-left: 30px;"><a href="#attr_ba_Activity__players">players</a>, <a href="#attr_ba_Activity__settings">settings</a>, <a href="#attr_ba_Activity__teams">teams</a></h5>
<h3 style="padding-left: 0px;">Attributes Defined Here:</h3>
<h5 style="padding-left: 30px;"><a href="#attr_ba_TeamGameActivity__map">map</a>, <a href="#attr_ba_TeamGameActivity__session">session</a>, <a href="#attr_ba_TeamGameActivity__stats">stats</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_TeamGameActivity__map"><strong>map</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"><a href="#class_ba_Map">ba.Map</a></span></p>
<p style="padding-left: 60px;">The map being used for this game.</p>

<p style="padding-left: 60px;">        Raises a <a href="#class_ba_NotFoundError">ba.NotFoundError</a> if the map does not currently exist.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_TeamGameActivity__session"><strong>session</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"><a href="#class_ba_Session">ba.Session</a></span></p>
<p style="padding-left: 60px;">The <a href="#class_ba_Session">ba.Session</a> this <a href="#class_ba_Activity">ba.Activity</a> belongs go.</p>

<p style="padding-left: 60px;">        Raises a <a href="#class_ba_SessionNotFoundError">ba.SessionNotFoundError</a> if the Session no longer exists.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_TeamGameActivity__stats"><strong>stats</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"><a href="#class_ba_Stats">ba.Stats</a></span></p>
<p style="padding-left: 60px;">The stats instance accessible while the activity is running.</p>

<p style="padding-left: 60px;">        If access is attempted before or after, raises a <a href="#class_ba_NotFoundError">ba.NotFoundError</a>.</p>

<h3 style="padding-left: 0px;">Methods Inherited:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_GameActivity__add_actor_weak_ref">add_actor_weak_ref()</a>, <a href="#method_ba_GameActivity__begin">begin()</a>, <a href="#method_ba_GameActivity__continue_or_end_game">continue_or_end_game()</a>, <a href="#method_ba_GameActivity__create_config_ui">create_config_ui()</a>, <a href="#method_ba_GameActivity__create_player_node">create_player_node()</a>, <a href="#method_ba_GameActivity__dep_is_present">dep_is_present()</a>, <a href="#method_ba_GameActivity__end_game">end_game()</a>, <a href="#method_ba_GameActivity__get_config_display_string">get_config_display_string()</a>, <a href="#method_ba_GameActivity__get_description">get_description()</a>, <a href="#method_ba_GameActivity__get_description_display_string">get_description_display_string()</a>, <a href="#method_ba_GameActivity__get_display_string">get_display_string()</a>, <a href="#method_ba_GameActivity__get_dynamic_deps">get_dynamic_deps()</a>, <a href="#method_ba_GameActivity__get_instance_description">get_instance_description()</a>, <a href="#method_ba_GameActivity__get_instance_display_string">get_instance_display_string()</a>, <a href="#method_ba_GameActivity__get_instance_scoreboard_description">get_instance_scoreboard_description()</a>, <a href="#method_ba_GameActivity__get_instance_scoreboard_display_string">get_instance_scoreboard_display_string()</a>, <a href="#method_ba_GameActivity__get_name">get_name()</a>, <a href="#method_ba_GameActivity__get_resolved_score_info">get_resolved_score_info()</a>, <a href="#method_ba_GameActivity__get_score_info">get_score_info()</a>, <a href="#method_ba_GameActivity__get_settings">get_settings()</a>, <a href="#method_ba_GameActivity__get_supported_maps">get_supported_maps()</a>, <a href="#method_ba_GameActivity__get_team_display_string">get_team_display_string()</a>, <a href="#method_ba_GameActivity__handlemessage">handlemessage()</a>, <a href="#method_ba_GameActivity__has_begun">has_begun()</a>, <a href="#method_ba_GameActivity__has_ended">has_ended()</a>, <a href="#method_ba_GameActivity__has_transitioned_in">has_transitioned_in()</a>, <a href="#method_ba_GameActivity__is_expired">is_expired()</a>, <a href="#method_ba_GameActivity__is_transitioning_out">is_transitioning_out()</a>, <a href="#method_ba_GameActivity__is_waiting_for_continue">is_waiting_for_continue()</a>, <a href="#method_ba_GameActivity__on_continue">on_continue()</a>, <a href="#method_ba_GameActivity__on_expire">on_expire()</a>, <a href="#method_ba_GameActivity__on_player_join">on_player_join()</a>, <a href="#method_ba_GameActivity__on_player_leave">on_player_leave()</a>, <a href="#method_ba_GameActivity__on_team_join">on_team_join()</a>, <a href="#method_ba_GameActivity__on_team_leave">on_team_leave()</a>, <a href="#method_ba_GameActivity__on_transition_out">on_transition_out()</a>, <a href="#method_ba_GameActivity__project_flag_stand">project_flag_stand()</a>, <a href="#method_ba_GameActivity__respawn_player">respawn_player()</a>, <a href="#method_ba_GameActivity__retain_actor">retain_actor()</a>, <a href="#method_ba_GameActivity__set_has_ended">set_has_ended()</a>, <a href="#method_ba_GameActivity__set_immediate_end">set_immediate_end()</a>, <a href="#method_ba_GameActivity__setup_standard_powerup_drops">setup_standard_powerup_drops()</a>, <a href="#method_ba_GameActivity__setup_standard_time_limit">setup_standard_time_limit()</a>, <a href="#method_ba_GameActivity__show_info">show_info()</a>, <a href="#method_ba_GameActivity__show_scoreboard_info">show_scoreboard_info()</a>, <a href="#method_ba_GameActivity__show_zoom_message">show_zoom_message()</a>, <a href="#method_ba_GameActivity__spawn_player">spawn_player()</a>, <a href="#method_ba_GameActivity__spawn_player_if_exists">spawn_player_if_exists()</a>, <a href="#method_ba_GameActivity__start_transition_in">start_transition_in()</a></h5>
<h3 style="padding-left: 0px;">Methods Defined or Overridden:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_TeamGameActivity____init__">&lt;constructor&gt;</a>, <a href="#method_ba_TeamGameActivity__end">end()</a>, <a href="#method_ba_TeamGameActivity__on_begin">on_begin()</a>, <a href="#method_ba_TeamGameActivity__on_transition_in">on_transition_in()</a>, <a href="#method_ba_TeamGameActivity__spawn_player_spaz">spawn_player_spaz()</a>, <a href="#method_ba_TeamGameActivity__supports_session_type">supports_session_type()</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_TeamGameActivity____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.TeamGameActivity(settings: Dict[str, Any])</span></p>

<p style="padding-left: 60px;">Instantiate the Activity.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_TeamGameActivity__end"><strong>end()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">end(self, results: Any = None, announce_winning_team: bool = True, announce_delay: float = 0.1, force: bool = False) -&gt; None</span></p>

<p style="padding-left: 60px;">End the game and announce the single winning team
unless 'announce_winning_team' is False.
(for results without a single most-important winner).</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_TeamGameActivity__on_begin"><strong>on_begin()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">on_begin(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Called once the previous <a href="#class_ba_Activity">ba.Activity</a> has finished transitioning out.</p>

<p style="padding-left: 60px;">At this point the activity's initial players and teams are filled in
and it should begin its actual game logic.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_TeamGameActivity__on_transition_in"><strong>on_transition_in()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">on_transition_in(self, music: str = None) -&gt; None</span></p>

<p style="padding-left: 60px;">Method override; optionally can
be passed a 'music' string which is the suggested type of
music to play during the game.
Note that in some cases music may be overridden by
the map or other factors, which is why you should pass
it in here instead of simply playing it yourself.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_TeamGameActivity__spawn_player_spaz"><strong>spawn_player_spaz()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">spawn_player_spaz(self, player: <a href="#class_ba_Player">ba.Player</a>, position: Sequence[float] = None, angle: float = None) -&gt; PlayerSpaz</span></p>

<p style="padding-left: 60px;">Method override; spawns and wires up a standard ba.PlayerSpaz for
a <a href="#class_ba_Player">ba.Player</a>.</p>

<p style="padding-left: 60px;">If position or angle is not supplied, a default will be chosen based
on the <a href="#class_ba_Player">ba.Player</a> and their <a href="#class_ba_Team">ba.Team</a>.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_TeamGameActivity__supports_session_type"><strong>supports_session_type()</strong></a></h4>
<h5 style="padding-left: 60px;"><span style="color: #CC6600;"><em>&lt;class method&gt;</span></em></h5>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">supports_session_type(sessiontype: Type[<a href="#class_ba_Session">ba.Session</a>]) -&gt; bool </span></p>

<p style="padding-left: 60px;">Class method override;
returns True for <a href="#class_ba_TeamsSession">ba.TeamsSessions</a> and <a href="#class_ba_FreeForAllSession">ba.FreeForAllSessions</a>;
False otherwise.</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_TeamGameResults">ba.TeamGameResults</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">
Results for a completed <a href="#class_ba_TeamGameActivity">ba.TeamGameActivity</a>.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a></p>

<p style="padding-left: 30px;">Upon completion, a game should fill one of these out and pass it to its
<a href="#method_ba_Activity__end">ba.Activity.end</a>() call.</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_TeamGameResults____init__">&lt;constructor&gt;</a>, <a href="#method_ba_TeamGameResults__get_lower_is_better">get_lower_is_better()</a>, <a href="#method_ba_TeamGameResults__get_player_info">get_player_info()</a>, <a href="#method_ba_TeamGameResults__get_score_name">get_score_name()</a>, <a href="#method_ba_TeamGameResults__get_score_type">get_score_type()</a>, <a href="#method_ba_TeamGameResults__get_team_score">get_team_score()</a>, <a href="#method_ba_TeamGameResults__get_team_score_str">get_team_score_str()</a>, <a href="#method_ba_TeamGameResults__get_teams">get_teams()</a>, <a href="#method_ba_TeamGameResults__get_winners">get_winners()</a>, <a href="#method_ba_TeamGameResults__get_winning_team">get_winning_team()</a>, <a href="#method_ba_TeamGameResults__has_score_for_team">has_score_for_team()</a>, <a href="#method_ba_TeamGameResults__set_game">set_game()</a>, <a href="#method_ba_TeamGameResults__set_team_score">set_team_score()</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_TeamGameResults____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.TeamGameResults()</span></p>

<p style="padding-left: 60px;">Instantiate a results instance.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_TeamGameResults__get_lower_is_better"><strong>get_lower_is_better()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_lower_is_better(self) -&gt; bool</span></p>

<p style="padding-left: 60px;">Return whether lower scores are better.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_TeamGameResults__get_player_info"><strong>get_player_info()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_player_info(self) -&gt; List[Dict[str, Any]]</span></p>

<p style="padding-left: 60px;">Get info about the players represented by the results.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_TeamGameResults__get_score_name"><strong>get_score_name()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_score_name(self) -&gt; str</span></p>

<p style="padding-left: 60px;">Get the name associated with scores ('points', etc).</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_TeamGameResults__get_score_type"><strong>get_score_type()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_score_type(self) -&gt; str</span></p>

<p style="padding-left: 60px;">Get the type of score.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_TeamGameResults__get_team_score"><strong>get_team_score()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_team_score(self, team: <a href="#class_ba_Team">ba.Team</a>) -&gt; Optional[int]</span></p>

<p style="padding-left: 60px;">Return the score for a given team.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_TeamGameResults__get_team_score_str"><strong>get_team_score_str()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_team_score_str(self, team: <a href="#class_ba_Team">ba.Team</a>) -&gt; <a href="#class_ba_Lstr">ba.Lstr</a></span></p>

<p style="padding-left: 60px;">Return the score for the given <a href="#class_ba_Team">ba.Team</a> as an Lstr.</p>

<p style="padding-left: 60px;">(properly formatted for the score type.)</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_TeamGameResults__get_teams"><strong>get_teams()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_teams(self) -&gt; List[<a href="#class_ba_Team">ba.Team</a>]</span></p>

<p style="padding-left: 60px;">Return all <a href="#class_ba_Team">ba.Teams</a> in the results.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_TeamGameResults__get_winners"><strong>get_winners()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_winners(self) -&gt; List[WinnerGroup]</span></p>

<p style="padding-left: 60px;">Get an ordered list of winner groups.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_TeamGameResults__get_winning_team"><strong>get_winning_team()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_winning_team(self) -&gt; Optional[<a href="#class_ba_Team">ba.Team</a>]</span></p>

<p style="padding-left: 60px;">Get the winning <a href="#class_ba_Team">ba.Team</a> if there is exactly one; None otherwise.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_TeamGameResults__has_score_for_team"><strong>has_score_for_team()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">has_score_for_team(self, team: <a href="#class_ba_Team">ba.Team</a>) -&gt; bool</span></p>

<p style="padding-left: 60px;">Return whether there is a score for a given team.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_TeamGameResults__set_game"><strong>set_game()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">set_game(self, game: <a href="#class_ba_GameActivity">ba.GameActivity</a>) -&gt; None</span></p>

<p style="padding-left: 60px;">Set the game instance these results are applying to.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_TeamGameResults__set_team_score"><strong>set_team_score()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">set_team_score(self, team: <a href="#class_ba_Team">ba.Team</a>, score: int) -&gt; None</span></p>

<p style="padding-left: 60px;">Set the score for a given <a href="#class_ba_Team">ba.Team</a>.</p>

<p style="padding-left: 60px;">This can be a number or None.
(see the none_is_winner arg in the constructor)</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_TeamNotFoundError">ba.TeamNotFoundError</a></strong></h3>
<p style="padding-left: 30px;">inherits from: <a href="#class_ba_NotFoundError">ba.NotFoundError</a>, Exception, BaseException</p>
<p style="padding-left: 30px;">Exception raised when an expected <a href="#class_ba_Team">ba.Team</a> does not exist.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Exception_Classes">Exception Classes</a>
</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<p style="padding-left: 30px;">&lt;all methods inherited from <a href="#class_ba_NotFoundError">ba.NotFoundError</a>&gt;</p>
<hr>
<h2><strong><a class="offsanchor" name="class_ba_TeamsSession">ba.TeamsSession</a></strong></h3>
<p style="padding-left: 30px;">inherits from: <a href="#class_ba_TeamBaseSession">ba.TeamBaseSession</a>, <a href="#class_ba_Session">ba.Session</a></p>
<p style="padding-left: 30px;"><a href="#class_ba_Session">ba.Session</a> type for teams mode games.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Gameplay_Classes">Gameplay Classes</a>
</p>

<h3 style="padding-left: 0px;">Attributes Inherited:</h3>
<h5 style="padding-left: 30px;"><a href="#attr_ba_Session__campaign">campaign</a>, <a href="#attr_ba_Session__lobby">lobby</a>, <a href="#attr_ba_Session__max_players">max_players</a>, <a href="#attr_ba_Session__min_players">min_players</a>, <a href="#attr_ba_Session__players">players</a>, <a href="#attr_ba_Session__teams">teams</a></h5>
<h3 style="padding-left: 0px;">Methods Inherited:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_TeamBaseSession__announce_game_results">announce_game_results()</a>, <a href="#method_ba_TeamBaseSession__begin_next_activity">begin_next_activity()</a>, <a href="#method_ba_TeamBaseSession__end">end()</a>, <a href="#method_ba_TeamBaseSession__end_activity">end_activity()</a>, <a href="#method_ba_TeamBaseSession__get_custom_menu_entries">get_custom_menu_entries()</a>, <a href="#method_ba_TeamBaseSession__get_ffa_series_length">get_ffa_series_length()</a>, <a href="#method_ba_TeamBaseSession__get_game_number">get_game_number()</a>, <a href="#method_ba_TeamBaseSession__get_max_players">get_max_players()</a>, <a href="#method_ba_TeamBaseSession__get_next_game_description">get_next_game_description()</a>, <a href="#method_ba_TeamBaseSession__get_series_length">get_series_length()</a>, <a href="#method_ba_TeamBaseSession__getactivity">getactivity()</a>, <a href="#method_ba_TeamBaseSession__handlemessage">handlemessage()</a>, <a href="#method_ba_TeamBaseSession__launch_end_session_activity">launch_end_session_activity()</a>, <a href="#method_ba_TeamBaseSession__on_activity_end">on_activity_end()</a>, <a href="#method_ba_TeamBaseSession__on_player_leave">on_player_leave()</a>, <a href="#method_ba_TeamBaseSession__on_player_request">on_player_request()</a>, <a href="#method_ba_TeamBaseSession__on_team_join">on_team_join()</a>, <a href="#method_ba_TeamBaseSession__on_team_leave">on_team_leave()</a>, <a href="#method_ba_TeamBaseSession__set_activity">set_activity()</a></h5>
<h3 style="padding-left: 0px;">Methods Defined or Overridden:</h3>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_TeamsSession____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.TeamsSession()</span></p>

<p style="padding-left: 60px;">Set up playlists and launches a <a href="#class_ba_Activity">ba.Activity</a> to accept joiners.</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_Texture">ba.Texture</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">A reference to a texture.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Asset_Classes">Asset Classes</a></p>

<p style="padding-left: 30px;">Use <a href="#function_ba_gettexture">ba.gettexture</a>() to instantiate one.</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_ThawMessage">ba.ThawMessage</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">Tells an object to stop being frozen.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Message_Classes">Message Classes</a>
</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_ThawMessage____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.ThawMessage()</span></p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_TimeFormat">ba.TimeFormat</a></strong></h3>
<p style="padding-left: 30px;">inherits from: enum.Enum</p>
<p style="padding-left: 30px;">Specifies the format time values are provided in.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Enums">Enums</a>
</p>

<h3 style="padding-left: 0px;">Values:</h3>
<ul>
<li>SECONDS</li>
<li>MILLISECONDS</li>
</ul>
<hr>
<h2><strong><a class="offsanchor" name="class_ba_Timer">ba.Timer</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">Timer(time: float, call: Callable[[], Any], repeat: bool = False,
  timetype: <a href="#class_ba_TimeType">ba.TimeType</a> = TimeType.SIM,
  timeformat: <a href="#class_ba_TimeFormat">ba.TimeFormat</a> = TimeFormat.SECONDS,
  suppress_format_warning: bool = False)</p>

<p style="padding-left: 30px;">Timers are used to run code at later points in time.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_General_Utility_Classes">General Utility Classes</a></p>

<p style="padding-left: 30px;">This class encapsulates a timer in the current <a href="#class_ba_Context">ba.Context</a>.
The underlying timer will be destroyed when either this object is
no longer referenced or when its Context (Activity, etc.) dies. If you
do not want to worry about keeping a reference to your timer around,
you should use the <a href="#function_ba_timer">ba.timer</a>() function instead.</p>

<p style="padding-left: 30px;">time: length of time (in seconds by default) that the timer will wait
before firing. Note that the actual delay experienced may vary
 depending on the timetype. (see below)</p>

<p style="padding-left: 30px;">call: A callable Python object. Note that the timer will retain a
strong reference to the callable for as long as it exists, so you
may want to look into concepts such as <a href="#class_ba_WeakCall">ba.WeakCall</a> if that is not
desired.</p>

<p style="padding-left: 30px;">repeat: if True, the timer will fire repeatedly, with each successive
firing having the same delay as the first.</p>

<p style="padding-left: 30px;">timetype can be either 'sim', 'base', or 'real'. It defaults to
'sim'. Types are explained below:</p>

<p style="padding-left: 30px;">'sim' time maps to local simulation time in <a href="#class_ba_Activity">ba.Activity</a> or <a href="#class_ba_Session">ba.Session</a>
Contexts. This means that it may progress slower in slow-motion play
modes, stop when the game is paused, etc.  This time type is not
available in UI contexts.</p>

<p style="padding-left: 30px;">'base' time is also linked to gameplay in <a href="#class_ba_Activity">ba.Activity</a> or <a href="#class_ba_Session">ba.Session</a>
Contexts, but it progresses at a constant rate regardless of
 slow-motion states or pausing.  It can, however, slow down or stop
in certain cases such as network outages or game slowdowns due to
cpu load. Like 'sim' time, this is unavailable in UI contexts.</p>

<p style="padding-left: 30px;">'real' time always maps to actual clock time with a bit of filtering
added, regardless of Context.  (the filtering prevents it from going
backwards or jumping forward by large amounts due to the app being
backgrounded, system time changing, etc.)
Real time timers are currently only available in the UI context.</p>

<p style="padding-left: 30px;">the 'timeformat' arg defaults to SECONDS but can also be MILLISECONDS
if you want to pass time as milliseconds.</p>

<pre style="padding-left: 30px;"><span style="color: #008800;"># example: use a Timer object to print repeatedly for a few seconds:</span>
def say_it():
    <a href="#function_ba_screenmessage">ba.screenmessage</a>('BADGER!')
def stop_saying_it():
    self.t = None
    <a href="#function_ba_screenmessage">ba.screenmessage</a>('MUSHROOM MUSHROOM!')
<span style="color: #008800;"># create our timer; it will run as long as we hold self.t</span>
self.t = <a href="#class_ba_Timer">ba.Timer</a>(0.3, say_it, repeat=True)
<span style="color: #008800;"># now fire off a one-shot timer to kill it</span>
<a href="#function_ba_timer">ba.timer</a>(3.89, stop_saying_it)</pre>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_TimeType">ba.TimeType</a></strong></h3>
<p style="padding-left: 30px;">inherits from: enum.Enum</p>
<p style="padding-left: 30px;">Specifies the type of time for various operations to target/use.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Enums">Enums</a></p>

<p style="padding-left: 30px;">    'sim' time is the local simulation time for an activity or session.
       It can proceed at different rates depending on game speed, stops
       for pauses, etc.</p>

<p style="padding-left: 30px;">    'base' is the baseline time for an activity or session.  It proceeds
       consistently regardless of game speed or pausing, but may stop during
       occurrences such as network outages.</p>

<p style="padding-left: 30px;">    'real' time is mostly based on clock time, with a few exceptions.  It may
       not advance while the app is backgrounded for instance.  (the engine
       attempts to prevent single large time jumps from occurring)
</p>

<h3 style="padding-left: 0px;">Values:</h3>
<ul>
<li>SIM</li>
<li>BASE</li>
<li>REAL</li>
</ul>
<hr>
<h2><strong><a class="offsanchor" name="class_ba_UIController">ba.UIController</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">Wrangles UILocations.</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_UIController____init__">&lt;constructor&gt;</a>, <a href="#method_ba_UIController__show_main_menu">show_main_menu()</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_UIController____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.UIController()</span></p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_UIController__show_main_menu"><strong>show_main_menu()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">show_main_menu(self, in_game: bool = True) -&gt; None</span></p>

<p style="padding-left: 60px;">Show the main menu, clearing other UIs from location stacks.</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_UILocation">ba.UILocation</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">Defines a specific 'place' in the UI the user can navigate to.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_User_Interface_Classes">User Interface Classes</a>
</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_UILocation____init__">&lt;constructor&gt;</a>, <a href="#method_ba_UILocation__push_location">push_location()</a>, <a href="#method_ba_UILocation__restore_state">restore_state()</a>, <a href="#method_ba_UILocation__save_state">save_state()</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_UILocation____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.UILocation()</span></p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_UILocation__push_location"><strong>push_location()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">push_location(self, location: str) -&gt; None</span></p>

<p style="padding-left: 60px;">Push a new location to the stack and transition to it.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_UILocation__restore_state"><strong>restore_state()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">restore_state(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Restore this instance's state from a dict.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_UILocation__save_state"><strong>save_state()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">save_state(self) -&gt; None</span></p>

<p style="padding-left: 60px;">Serialize this instance's state to a dict.</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_UILocationWindow">ba.UILocationWindow</a></strong></h3>
<p style="padding-left: 30px;">inherits from: <a href="#class_ba_UILocation">ba.UILocation</a></p>
<p style="padding-left: 30px;">A UILocation consisting of a single root window widget.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_User_Interface_Classes">User Interface Classes</a>
</p>

<h3 style="padding-left: 0px;">Methods Inherited:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_UILocation__push_location">push_location()</a>, <a href="#method_ba_UILocation__restore_state">restore_state()</a>, <a href="#method_ba_UILocation__save_state">save_state()</a></h5>
<h3 style="padding-left: 0px;">Methods Defined or Overridden:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_UILocationWindow____init__">&lt;constructor&gt;</a>, <a href="#method_ba_UILocationWindow__get_root_widget">get_root_widget()</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_UILocationWindow____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.UILocationWindow()</span></p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_UILocationWindow__get_root_widget"><strong>get_root_widget()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_root_widget(self) -&gt; <a href="#class_ba_Widget">ba.Widget</a></span></p>

<p style="padding-left: 60px;">Return the root widget for this window.</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_Vec3">ba.Vec3</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">A vector of 3 floats.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_General_Utility_Classes">General Utility Classes</a></p>

<p style="padding-left: 30px;">These can be created the following ways (checked in this order):
- with no args, all values are set to 0
- with a single numeric arg, all values are set to that value
- with a single three-member sequence arg, sequence values are copied
- otherwise assumes individual x/y/z args (positional or keywords)</p>

<h3 style="padding-left: 0px;">Attributes:</h3>
<h5 style="padding-left: 30px;"><a href="#attr_ba_Vec3__x">x</a>, <a href="#attr_ba_Vec3__y">y</a>, <a href="#attr_ba_Vec3__z">z</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Vec3__x"><strong>x</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"> float</span></p>
<p style="padding-left: 60px;">The vector's X component.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Vec3__y"><strong>y</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"> float</span></p>
<p style="padding-left: 60px;">The vector's Y component.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="attr_ba_Vec3__z"><strong>z</strong></a></h4>
<p style="padding-left: 60px;"><span style="color: #666677;"> float</span></p>
<p style="padding-left: 60px;">The vector's Z component.</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_Vec3__cross">cross()</a>, <a href="#method_ba_Vec3__dot">dot()</a>, <a href="#method_ba_Vec3__length">length()</a>, <a href="#method_ba_Vec3__normalized">normalized()</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Vec3__cross"><strong>cross()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">cross(other: Vec3) -&gt; Vec3</span></p>

<p style="padding-left: 60px;">Returns the cross product of this vector and another.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Vec3__dot"><strong>dot()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">dot(other: Vec3) -&gt; float</span></p>

<p style="padding-left: 60px;">Returns the dot product of this vector and another.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Vec3__length"><strong>length()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">length() -&gt; float</span></p>

<p style="padding-left: 60px;">Returns the length of the vector.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Vec3__normalized"><strong>normalized()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">normalized() -&gt; Vec3</span></p>

<p style="padding-left: 60px;">Returns a normalized version of the vector.</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_WeakCall">ba.WeakCall</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">Wrap a callable and arguments into a single callable object.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_General_Utility_Classes">General Utility Classes</a></p>

<p style="padding-left: 30px;">    When passed a bound method as the callable, the instance portion
    of it is weak-referenced, meaning the underlying instance is
    free to die if all other references to it go away. Should this
    occur, calling the WeakCall is simply a no-op.</p>

<p style="padding-left: 30px;">    Think of this as a handy way to tell an object to do something
    at some point in the future if it happens to still exist.</p>

<pre style="padding-left: 30px;"><span style="color: #008800;">    # EXAMPLE A: this code will create a FooClass instance and call its</span>
<span style="color: #008800;">    # bar() method 5 seconds later; it will be kept alive even though</span>
<span style="color: #008800;">    # we overwrite its variable with None because the bound method</span>
<span style="color: #008800;">    # we pass as a timer callback (foo.bar) strong-references it</span>
    foo = FooClass()
    <a href="#function_ba_timer">ba.timer</a>(5.0, foo.bar)
    foo = None</pre>

<pre style="padding-left: 30px;"><span style="color: #008800;">    # EXAMPLE B: this code will *not* keep our object alive; it will die</span>
<span style="color: #008800;">    # when we overwrite it with None and the timer will be a no-op when it</span>
<span style="color: #008800;">    # fires</span>
    foo = FooClass()
    <a href="#function_ba_timer">ba.timer</a>(5.0, <a href="#class_ba_WeakCall">ba.WeakCall</a>(foo.bar))
    foo = None</pre>

<p style="padding-left: 30px;">    Note: additional args and keywords you provide to the WeakCall()
    constructor are stored as regular strong-references; you'll need
    to wrap them in weakrefs manually if desired.
</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_WeakCall____init__"><strong>&lt;constructor&gt;</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">ba.WeakCall(*args: Any, **keywds: Any)</span></p>

<p style="padding-left: 60px;">Instantiate a WeakCall; pass a callable as the first
arg, followed by any number of arguments or keywords.</p>

<pre style="padding-left: 60px;"><span style="color: #008800;"># example: wrap a method call with some positional and</span>
<span style="color: #008800;"># keyword args:</span>
myweakcall = ba.WeakCall(myobj.dostuff, argval1, namedarg=argval2)</pre>

<pre style="padding-left: 60px;"><span style="color: #008800;"># Now we have a single callable to run that whole mess.</span>
<span style="color: #008800;"># The same as calling myobj.dostuff(argval1, namedarg=argval2)</span>
<span style="color: #008800;"># (provided my_obj still exists; this will do nothing otherwise)</span>
myweakcall()</pre>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_Widget">ba.Widget</a></strong></h3>
<p style="padding-left: 30px;"><em>&lt;top level class&gt;</em>
</p>
<p style="padding-left: 30px;">Internal type for low level UI elements; buttons, windows, etc.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_User_Interface_Classes">User Interface Classes</a></p>

<p style="padding-left: 30px;">This class represents a weak reference to a widget object
in the internal c++ layer. Currently, functions such as
<a href="#function_ba_buttonwidget">ba.buttonwidget</a>() must be used to instantiate or edit these.</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<h5 style="padding-left: 30px;"><a href="#method_ba_Widget__activate">activate()</a>, <a href="#method_ba_Widget__add_delete_callback">add_delete_callback()</a>, <a href="#method_ba_Widget__delete">delete()</a>, <a href="#method_ba_Widget__exists">exists()</a>, <a href="#method_ba_Widget__get_children">get_children()</a>, <a href="#method_ba_Widget__get_screen_space_center">get_screen_space_center()</a>, <a href="#method_ba_Widget__get_selected_child">get_selected_child()</a>, <a href="#method_ba_Widget__get_widget_type">get_widget_type()</a></h5>
<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Widget__activate"><strong>activate()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">activate() -&gt; None</span></p>

<p style="padding-left: 60px;">Activates a widget; the same as if it had been clicked.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Widget__add_delete_callback"><strong>add_delete_callback()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">add_delete_callback(call: Callable) -&gt; None</span></p>

<p style="padding-left: 60px;">Add a call to be run immediately after this widget is destroyed.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Widget__delete"><strong>delete()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">delete(ignore_missing: bool = True) -&gt; None</span></p>

<p style="padding-left: 60px;">Delete the Widget.  Ignores already-deleted Widgets if ignore_missing
  is True; otherwise an Exception is thrown.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Widget__exists"><strong>exists()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">exists() -&gt; bool</span></p>

<p style="padding-left: 60px;">Returns whether the Widget still exists.
Most functionality will fail on a nonexistent widget.</p>

<p style="padding-left: 60px;">Note that you can also use the boolean operator for this same
functionality, so a statement such as "if mywidget" will do
the right thing both for Widget objects and values of None.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Widget__get_children"><strong>get_children()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_children() -&gt; List[<a href="#class_ba_Widget">ba.Widget</a>]</span></p>

<p style="padding-left: 60px;">Returns any child Widgets of this Widget.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Widget__get_screen_space_center"><strong>get_screen_space_center()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_screen_space_center() -&gt; Tuple[float, float]</span></p>

<p style="padding-left: 60px;">Returns the coords of the Widget center relative to the center of the
screen. This can be useful for placing pop-up windows and other special
cases.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Widget__get_selected_child"><strong>get_selected_child()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_selected_child() -&gt; Optional[<a href="#class_ba_Widget">ba.Widget</a>]</span></p>

<p style="padding-left: 60px;">Returns the selected child Widget or None if nothing is selected.</p>

<h4 style="padding-left: 30px;"><a class="offsanchor" name="method_ba_Widget__get_widget_type"><strong>get_widget_type()</strong></a></h4>
<p style="padding-left: 110px; text-indent: -50px;"><span style="color: #666677;">get_widget_type() -&gt; str</span></p>

<p style="padding-left: 60px;">Return the internal type of the Widget as a string.  Note that this is
different from the Python <a href="#class_ba_Widget">ba.Widget</a> type, which is the same for all
widgets.</p>

<hr>
<h2><strong><a class="offsanchor" name="class_ba_WidgetNotFoundError">ba.WidgetNotFoundError</a></strong></h3>
<p style="padding-left: 30px;">inherits from: <a href="#class_ba_NotFoundError">ba.NotFoundError</a>, Exception, BaseException</p>
<p style="padding-left: 30px;">Exception raised when an expected <a href="#class_ba_Widget">ba.Widget</a> does not exist.</p>

<p style="padding-left: 30px;">Category: <a href="#class_category_Exception_Classes">Exception Classes</a>
</p>

<h3 style="padding-left: 0px;">Methods:</h3>
<p style="padding-left: 30px;">&lt;all methods inherited from <a href="#class_ba_NotFoundError">ba.NotFoundError</a>&gt;</p>
<hr>
<h2><strong><a class="offsanchor" name="function_ba_animate">ba.animate()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">animate(node: <a href="#class_ba_Node">ba.Node</a>, attr: str, keys: Dict[float, float], loop: bool = False, offset: float = 0, timetype: <a href="#class_ba_TimeType">ba.TimeType</a> = &lt;TimeType.SIM: 0&gt;, timeformat: <a href="#class_ba_TimeFormat">ba.TimeFormat</a> = &lt;TimeFormat.SECONDS: 0&gt;, suppress_format_warning: bool = False) -&gt; <a href="#class_ba_Node">ba.Node</a></span></p>

<p style="padding-left: 30px;">Animate values on a target <a href="#class_ba_Node">ba.Node</a>.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_Gameplay_Functions">Gameplay Functions</a></p>

<p style="padding-left: 30px;">Creates an 'animcurve' node with the provided values and time as an input,
connect it to the provided attribute, and set it to die with the target.
Key values are provided as time:value dictionary pairs.  Time values are
relative to the current time. By default, times are specified in seconds,
but timeformat can also be set to MILLISECONDS to recreate the old behavior
(prior to ba 1.5) of taking milliseconds. Returns the animcurve node.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_animate_array">ba.animate_array()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">animate_array(node: <a href="#class_ba_Node">ba.Node</a>, attr: str, size: int, keys: Dict[float, Sequence[float]], loop: bool = False, offset: float = 0, timetype: <a href="#class_ba_TimeType">ba.TimeType</a> = &lt;TimeType.SIM: 0&gt;, timeformat: <a href="#class_ba_TimeFormat">ba.TimeFormat</a> = &lt;TimeFormat.SECONDS: 0&gt;, suppress_format_warning: bool = False) -&gt; None</span></p>

<p style="padding-left: 30px;">Animate an array of values on a target <a href="#class_ba_Node">ba.Node</a>.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_Gameplay_Functions">Gameplay Functions</a></p>

<p style="padding-left: 30px;">Like <a href="#function_ba_animate">ba.animate</a>(), but operates on array attributes.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_buttonwidget">ba.buttonwidget()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">buttonwidget(edit: <a href="#class_ba_Widget">ba.Widget</a> = None,
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

<p style="padding-left: 30px;">Create or edit a button widget.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_User_Interface_Functions">User Interface Functions</a></p>

<p style="padding-left: 30px;">Pass a valid existing <a href="#class_ba_Widget">ba.Widget</a> as 'edit' to modify it; otherwise
a new one is created and returned. Arguments that are not set to None
are applied to the Widget.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_cameraflash">ba.cameraflash()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">cameraflash(duration: float = 999.0) -&gt; None</span></p>

<p style="padding-left: 30px;">Create a strobing camera flash effect.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_Gameplay_Functions">Gameplay Functions</a></p>

<p style="padding-left: 30px;">(as seen when a team wins a game)
Duration is in seconds.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_camerashake">ba.camerashake()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">camerashake(intensity: float = 1.0) -&gt; None</span></p>

<p style="padding-left: 30px;">Shake the camera.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_Gameplay_Functions">Gameplay Functions</a></p>

<p style="padding-left: 30px;">Note that some cameras and/or platforms (such as VR) may not display
camera-shake, so do not rely on this always being visible to the
player as a gameplay cue.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_charstr">ba.charstr()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">charstr(char_id: <a href="#class_ba_SpecialChar">ba.SpecialChar</a>) -&gt; str</span></p>

<p style="padding-left: 30px;">Get a unicode string representing a special character.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p style="padding-left: 30px;">Note that these utilize the private-use block of unicode characters
(U+E000-U+F8FF) and are specific to the game; exporting or rendering
them elsewhere will be meaningless.</p>

<p style="padding-left: 30px;">see <a href="#class_ba_SpecialChar">ba.SpecialChar</a> for the list of available characters.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_checkboxwidget">ba.checkboxwidget()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">checkboxwidget(edit: <a href="#class_ba_Widget">ba.Widget</a> = None,
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

<p style="padding-left: 30px;">Create or edit a check-box widget.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_User_Interface_Functions">User Interface Functions</a></p>

<p style="padding-left: 30px;">Pass a valid existing <a href="#class_ba_Widget">ba.Widget</a> as 'edit' to modify it; otherwise
a new one is created and returned. Arguments that are not set to None
are applied to the Widget.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_columnwidget">ba.columnwidget()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">columnwidget(edit: <a href="#class_ba_Widget">ba.Widget</a> = None,
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
  bottom_border: float = None) -&gt; <a href="#class_ba_Widget">ba.Widget</a></span></p>

<p style="padding-left: 30px;">Create or edit a column widget.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_User_Interface_Functions">User Interface Functions</a></p>

<p style="padding-left: 30px;">Pass a valid existing <a href="#class_ba_Widget">ba.Widget</a> as 'edit' to modify it; otherwise
a new one is created and returned. Arguments that are not set to None
are applied to the Widget.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_containerwidget">ba.containerwidget()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">containerwidget(edit: <a href="#class_ba_Widget">ba.Widget</a> = None,
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
  selection_loop_to_parent: bool = None,
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

<p style="padding-left: 30px;">Create or edit a container widget.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_User_Interface_Functions">User Interface Functions</a></p>

<p style="padding-left: 30px;">Pass a valid existing <a href="#class_ba_Widget">ba.Widget</a> as 'edit' to modify it; otherwise
a new one is created and returned. Arguments that are not set to None
are applied to the Widget.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_do_once">ba.do_once()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">do_once() -&gt; bool</span></p>

<p style="padding-left: 30px;">Register a call at a location and return whether one already happened.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p style="padding-left: 30px;">This is used by 'print_once()' type calls to keep from overflowing
logs. The call functions by registering the filename and line where
The call is made from.  Returns True if this location has not been
registered already, and False if it has.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_emitfx">ba.emitfx()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">emitfx(position: Sequence[float],
  velocity: Optional[Sequence[float]] = None,
  count: int = 10, scale: float = 1.0, spread: float = 1.0,
  chunk_type: str = 'rock', emit_type: str ='chunks',
  tendril_type: str = 'smoke') -&gt; None</span></p>

<p style="padding-left: 30px;">Emit particles, smoke, etc. into the fx sim layer.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_Gameplay_Functions">Gameplay Functions</a></p>

<p style="padding-left: 30px;">The fx sim layer is a secondary dynamics simulation that runs in
the background and just looks pretty; it does not affect gameplay.
Note that the actual amount emitted may vary depending on graphics
settings, exiting element counts, or other factors.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_get_collision_info">ba.get_collision_info()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">get_collision_info(*args: Any) -&gt; Any</span></p>

<p style="padding-left: 30px;">Return collision related values</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_Gameplay_Functions">Gameplay Functions</a></p>

<p style="padding-left: 30px;">Returns a single collision value or tuple of values such as location,
depth, nodes involved, etc. Only call this in the handler of a
collision-triggered callback or message</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_get_valid_languages">ba.get_valid_languages()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">get_valid_languages() -&gt; List[str]</span></p>

<p style="padding-left: 30px;">Return a list containing names of all available languages.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p style="padding-left: 30px;">Languages that may be present but are not displayable on the running
version of the game are ignored.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_getactivity">ba.getactivity()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">getactivity(doraise: bool = True) -&gt; <a href="#class_ba_Activity">ba.Activity</a></span></p>

<p style="padding-left: 30px;">Returns the current <a href="#class_ba_Activity">ba.Activity</a> instance.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_Gameplay_Functions">Gameplay Functions</a></p>

<p style="padding-left: 30px;">Note that this is based on context; thus code run in a timer generated
in Activity 'foo' will properly return 'foo' here, even if another
Activity has since been created or is transitioning in.
If there is no current Activity an Exception is raised, or if doraise is
False then None is returned instead.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_getcollidemodel">ba.getcollidemodel()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">getcollidemodel(name: str) -&gt; <a href="#class_ba_CollideModel">ba.CollideModel</a></span></p>

<p style="padding-left: 30px;">Return a collide-model, loading it if necessary.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_Asset_Functions">Asset Functions</a></p>

<p style="padding-left: 30px;">Collide-models are used in physics calculations for such things as
terrain.</p>

<p style="padding-left: 30px;">Note that this function returns immediately even if the media has yet
to be loaded. To avoid hitches, instantiate your media objects in
advance of when you will be using them, allowing time for them to load
in the background if necessary.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_getmaps">ba.getmaps()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">getmaps(playtype: str) -&gt; List[str]</span></p>

<p style="padding-left: 30px;">Return a list of <a href="#class_ba_Map">ba.Map</a> types supporting a playtype str.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_Asset_Functions">Asset Functions</a></p>

<p style="padding-left: 30px;">Maps supporting a given playtype must provide a particular set of
features and lend themselves to a certain style of play.</p>

<p style="padding-left: 30px;"><strong>Play Types:</strong></p>

<p style="padding-left: 30px;">'melee'
  General fighting map.
  Has one or more 'spawn' locations.</p>

<p style="padding-left: 30px;">'team_flag'
  For games such as Capture The Flag where each team spawns by a flag.
  Has two or more 'spawn' locations, each with a corresponding 'flag'
  location (based on index).</p>

<p style="padding-left: 30px;">'single_flag'
  For games such as King of the Hill or Keep Away where multiple teams
  are fighting over a single flag.
  Has two or more 'spawn' locations and 1 'flag_default' location.</p>

<p style="padding-left: 30px;">'conquest'
  For games such as Conquest where flags are spread throughout the map
  - has 2+ 'flag' locations, 2+ 'spawn_by_flag' locations.</p>

<p style="padding-left: 30px;">'king_of_the_hill' - has 2+ 'spawn' locations, 1+ 'flag_default' locations,
                     and 1+ 'powerup_spawn' locations</p>

<p style="padding-left: 30px;">'hockey'
  For hockey games.
  Has two 'goal' locations, corresponding 'spawn' locations, and one
  'flag_default' location (for where puck spawns)</p>

<p style="padding-left: 30px;">'football'
  For football games.
  Has two 'goal' locations, corresponding 'spawn' locations, and one
  'flag_default' location (for where flag/ball/etc. spawns)</p>

<p style="padding-left: 30px;">'race'
  For racing games where players much touch each region in order.
  Has two or more 'race_point' locations.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_getmodel">ba.getmodel()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">getmodel(name: str) -&gt; <a href="#class_ba_Model">ba.Model</a></span></p>

<p style="padding-left: 30px;">Return a model, loading it if necessary.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_Asset_Functions">Asset Functions</a></p>

<p style="padding-left: 30px;">Note that this function returns immediately even if the media has yet
to be loaded. To avoid hitches, instantiate your media objects in
advance of when you will be using them, allowing time for them to load
in the background if necessary.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_getnodes">ba.getnodes()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">getnodes() -&gt; list</span></p>

<p style="padding-left: 30px;">Return all nodes in the current <a href="#class_ba_Context">ba.Context</a>.
Category: <a href="#function_category_Gameplay_Functions">Gameplay Functions</a></p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_getsession">ba.getsession()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">getsession(doraise: bool = True) -&gt; <a href="#class_ba_Session">ba.Session</a></span></p>

<p style="padding-left: 30px;">Category: <a href="#function_category_Gameplay_Functions">Gameplay Functions</a></p>

<p style="padding-left: 30px;">Returns the current <a href="#class_ba_Session">ba.Session</a> instance.
Note that this is based on context; thus code being run in the UI
context will return the UI context here even if a game Session also
exists, etc. If there is no current Session, an Exception is raised, or
if doraise is False then None is returned instead.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_getsound">ba.getsound()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">getsound(name: str) -&gt; <a href="#class_ba_Sound">ba.Sound</a></span></p>

<p style="padding-left: 30px;">Return a sound, loading it if necessary.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_Asset_Functions">Asset Functions</a></p>

<p style="padding-left: 30px;">Note that this function returns immediately even if the media has yet
to be loaded. To avoid hitches, instantiate your media objects in
advance of when you will be using them, allowing time for them to load
in the background if necessary.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_gettexture">ba.gettexture()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">gettexture(name: str) -&gt; <a href="#class_ba_Texture">ba.Texture</a></span></p>

<p style="padding-left: 30px;">Return a texture, loading it if necessary.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_Asset_Functions">Asset Functions</a></p>

<p style="padding-left: 30px;">Note that this function returns immediately even if the media has yet
to be loaded. To avoid hitches, instantiate your media objects in
advance of when you will be using them, allowing time for them to load
in the background if necessary.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_hscrollwidget">ba.hscrollwidget()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">hscrollwidget(edit: <a href="#class_ba_Widget">ba.Widget</a> = None, parent: <a href="#class_ba_Widget">ba.Widget</a> = None,
  size: Sequence[float] = None, position: Sequence[float] = None,
  background: bool = None, selected_child: <a href="#class_ba_Widget">ba.Widget</a> = None,
  capture_arrows: bool = None,
  on_select_call: Callable[[], None] = None,
  center_small_content: bool = None, color: Sequence[float] = None,
  highlight: bool = None, border_opacity: float = None,
  simple_culling_h: float = None)  -&gt; <a href="#class_ba_Widget">ba.Widget</a></span></p>

<p style="padding-left: 30px;">Create or edit a horizontal scroll widget.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_User_Interface_Functions">User Interface Functions</a></p>

<p style="padding-left: 30px;">Pass a valid existing <a href="#class_ba_Widget">ba.Widget</a> as 'edit' to modify it; otherwise
a new one is created and returned. Arguments that are not set to None
are applied to the Widget.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_imagewidget">ba.imagewidget()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">imagewidget(edit: <a href="#class_ba_Widget">ba.Widget</a> = None, parent: <a href="#class_ba_Widget">ba.Widget</a> = None,
  size: Sequence[float] = None, position: Sequence[float] = None,
  color: Sequence[float] = None, texture: <a href="#class_ba_Texture">ba.Texture</a> = None,
  opacity: float = None, model_transparent: <a href="#class_ba_Model">ba.Model</a> = None,
  model_opaque: <a href="#class_ba_Model">ba.Model</a> = None, has_alpha_channel: bool = True,
  tint_texture: <a href="#class_ba_Texture">ba.Texture</a> = None, tint_color: Sequence[float] = None,
  transition_delay: float = None, draw_controller: <a href="#class_ba_Widget">ba.Widget</a> = None,
  tint2_color: Sequence[float] = None, tilt_scale: float = None,
  mask_texture: <a href="#class_ba_Texture">ba.Texture</a> = None, radial_amount: float = None)
  -&gt; <a href="#class_ba_Widget">ba.Widget</a></span></p>

<p style="padding-left: 30px;">Create or edit an image widget.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_User_Interface_Functions">User Interface Functions</a></p>

<p style="padding-left: 30px;">Pass a valid existing <a href="#class_ba_Widget">ba.Widget</a> as 'edit' to modify it; otherwise
a new one is created and returned. Arguments that are not set to None
are applied to the Widget.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_is_browser_likely_available">ba.is_browser_likely_available()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">is_browser_likely_available() -&gt; bool</span></p>

<p style="padding-left: 30px;">Return whether a browser likely exists on the current device.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p style="padding-left: 30px;">If this returns False you may want to avoid calling ba.show_url()
with any lengthy addresses. (ba.show_url() will display an address
as a string in a window if unable to bring up a browser, but that
is only useful for simple URLs.)</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_is_point_in_box">ba.is_point_in_box()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">is_point_in_box(pnt: Sequence[float], box: Sequence[float]) -&gt; bool</span></p>

<p style="padding-left: 30px;">Return whether a given point is within a given box.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p style="padding-left: 30px;">For use with standard def boxes (position|rotate|scale).</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_log">ba.log()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">log(message: str, to_console: bool = True, newline: bool = True,
  to_server: bool = True) -&gt; None</span></p>

<p style="padding-left: 30px;">Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p style="padding-left: 30px;">Log a message. This goes to the default logging mechanism depending
on the platform (stdout on mac, android log on android, etc).</p>

<p style="padding-left: 30px;">Log messages also go to the in-game console unless 'to_console'
is False. They are also sent to the master-server for use in analyzing
issues unless to_server is False.</p>

<p style="padding-left: 30px;">Python's standard print() is wired to call this (with default values)
so in most cases you can just use that.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_new_activity">ba.new_activity()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">new_activity(activity_type: Type[<a href="#class_ba_Activity">ba.Activity</a>],
  settings: dict = None) -&gt; <a href="#class_ba_Activity">ba.Activity</a></span></p>

<p style="padding-left: 30px;">Instantiates a <a href="#class_ba_Activity">ba.Activity</a> given a type object.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p style="padding-left: 30px;">Activities require special setup and thus cannot be directly
instantiated; You must go through this function.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_newnode">ba.newnode()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">newnode(type: str, owner: Union[Node, <a href="#class_ba_Actor">ba.Actor</a>] = None,
attrs: dict = None, name: str = None, delegate: Any = None)
 -&gt; Node</span></p>

<p style="padding-left: 30px;">Add a node of the given type to the game.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_Gameplay_Functions">Gameplay Functions</a></p>

<p style="padding-left: 30px;">If a dict is provided for 'attributes', the node's initial attributes
will be set based on them.</p>

<p style="padding-left: 30px;">'name', if provided, will be stored with the node purely for debugging
purposes. If no name is provided, an automatic one will be generated
such as 'terrain@foo.py:30'.</p>

<p style="padding-left: 30px;">If 'delegate' is provided, Python messages sent to the node will go to
that object's handlemessage() method. Note that the delegate is stored
as a weak-ref, so the node itself will not keep the object alive.</p>

<p style="padding-left: 30px;">if 'owner' is provided, the node will be automatically killed when that
object dies. 'owner' can be another node or a <a href="#class_ba_Actor">ba.Actor</a></p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_normalized_color">ba.normalized_color()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">normalized_color(color: Sequence[float]) -&gt; Tuple[float, ...]</span></p>

<p style="padding-left: 30px;">Scale a color so its largest value is 1; useful for coloring lights.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_open_url">ba.open_url()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">open_url(address: str) -&gt; None</span></p>

<p style="padding-left: 30px;">Open a provided URL.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p style="padding-left: 30px;">Open the provided url in a web-browser, or display the URL
string in a window if that isn't possible.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_playsound">ba.playsound()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">playsound(sound: Sound, volume: float = 1.0,
  position: Sequence[float] = None, host_only: bool = False) -&gt; None</span></p>

<p style="padding-left: 30px;">Play a <a href="#class_ba_Sound">ba.Sound</a> a single time.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_Gameplay_Functions">Gameplay Functions</a></p>

<p style="padding-left: 30px;">If position is not provided, the sound will be at a constant volume
everywhere.  Position should be a float tuple of size 3.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_print_error">ba.print_error()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">print_error(err_str: str, once: bool = False) -&gt; None</span></p>

<p style="padding-left: 30px;">Print info about an error along with pertinent context state.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p style="padding-left: 30px;">Prints all positional arguments provided along with various info about the
current context.
Pass the keyword 'once' as True if you want the call to only happen
one time from an exact calling location.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_print_exception">ba.print_exception()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">print_exception(*args: Any, **keywds: Any) -&gt; None</span></p>

<p style="padding-left: 30px;">Print info about an exception along with pertinent context state.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p style="padding-left: 30px;">Prints all arguments provided along with various info about the
current context and the outstanding exception.
Pass the keyword 'once' as True if you want the call to only happen
one time from an exact calling location.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_printnodes">ba.printnodes()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">printnodes() -&gt; None</span></p>

<p style="padding-left: 30px;">Print various info about existing nodes; useful for debugging.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_Gameplay_Functions">Gameplay Functions</a></p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_printobjects">ba.printobjects()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">printobjects() -&gt; None</span></p>

<p style="padding-left: 30px;">Print debugging info about game objects.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p style="padding-left: 30px;">This call only functions in debug builds of the game.
It prints various info about the current object count, etc.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_pushcall">ba.pushcall()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">pushcall(call: Callable, from_other_thread: bool = False) -&gt; None</span></p>

<p style="padding-left: 30px;">Pushes a call onto the event loop to be run during the next cycle.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p style="padding-left: 30px;">This can be handy for calls that are disallowed from within other
callbacks, etc.</p>

<p style="padding-left: 30px;">This call expects to be used in the game thread, and will automatically
save and restore the <a href="#class_ba_Context">ba.Context</a> to behave seamlessly.</p>

<p style="padding-left: 30px;">If you want to push a call from outside of the game thread,
however, you can pass 'from_other_thread' as True. In this case
the call will always run in the UI context on the game thread.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_quit">ba.quit()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">quit(soft: bool = False, back: bool = False) -&gt; None</span></p>

<p style="padding-left: 30px;">Quit the game.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p style="padding-left: 30px;">On systems like android, 'soft' will end the activity but keep the
app running.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_rowwidget">ba.rowwidget()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">rowwidget(edit: Widget =None, parent: Widget =None,
  size: Sequence[float] = None,
  position: Sequence[float] = None,
  background: bool = None, selected_child: Widget = None,
  visible_child: Widget = None) -&gt; Widget</span></p>

<p style="padding-left: 30px;">Create or edit a row widget.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_User_Interface_Functions">User Interface Functions</a></p>

<p style="padding-left: 30px;">Pass a valid existing <a href="#class_ba_Widget">ba.Widget</a> as 'edit' to modify it; otherwise
a new one is created and returned. Arguments that are not set to None
are applied to the Widget.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_safecolor">ba.safecolor()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">safecolor(color: Sequence[float], target_intensity: float = 0.6)
  -&gt; Tuple[float, ...]</span></p>

<p style="padding-left: 30px;">Given a color tuple, return a color safe to display as text.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p style="padding-left: 30px;">Accepts tuples of length 3 or 4. This will slightly brighten very
dark colors, etc.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_screenmessage">ba.screenmessage()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">screenmessage(message: Union[str, <a href="#class_ba_Lstr">ba.Lstr</a>],
  color: Sequence[float] = None, top: bool = False,
  image: Dict[str, Any] = None, log: bool = False,
  clients: Sequence[int] = None, transient: bool = False) -&gt; None</span></p>

<p style="padding-left: 30px;">Print a message to the local client's screen, in a given color.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p style="padding-left: 30px;">If 'top' is True, the message will go to the top message area.
For 'top' messages, 'image' can be a texture to display alongside the
message.
If 'log' is True, the message will also be printed to the output log
'clients' can be a list of client-ids the message should be sent to,
or None to specify that everyone should receive it.
If 'transient' is True, the message will not be included in the
game-stream and thus will not show up when viewing replays.
Currently the 'clients' option only works for transient messages.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_scrollwidget">ba.scrollwidget()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">scrollwidget(edit: <a href="#class_ba_Widget">ba.Widget</a> = None, parent: <a href="#class_ba_Widget">ba.Widget</a> = None,
  size: Sequence[float] = None, position: Sequence[float] = None,
  background: bool = None, selected_child: <a href="#class_ba_Widget">ba.Widget</a> = None,
  capture_arrows: bool = False, on_select_call: Callable = None,
  center_small_content: bool = None, color: Sequence[float] = None,
  highlight: bool = None, border_opacity: float = None,
  simple_culling_v: float = None) -&gt; <a href="#class_ba_Widget">ba.Widget</a></span></p>

<p style="padding-left: 30px;">Create or edit a scroll widget.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_User_Interface_Functions">User Interface Functions</a></p>

<p style="padding-left: 30px;">Pass a valid existing <a href="#class_ba_Widget">ba.Widget</a> as 'edit' to modify it; otherwise
a new one is created and returned. Arguments that are not set to None
are applied to the Widget.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_set_analytics_screen">ba.set_analytics_screen()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">set_analytics_screen(screen: str) -&gt; None</span></p>

<p style="padding-left: 30px;">Used for analytics to see where in the app players spend their time.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p style="padding-left: 30px;">Generally called when opening a new window or entering some UI.
'screen' should be a string description of an app location
('Main Menu', etc.)</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_setlanguage">ba.setlanguage()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">setlanguage(language: Optional[str], print_change: bool = True, store_to_config: bool = True) -&gt; None</span></p>

<p style="padding-left: 30px;">Set the active language used for the game.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p style="padding-left: 30px;">Pass None to use OS default language.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_setmusic">ba.setmusic()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">setmusic(musictype: Optional[str], continuous: bool = False) -&gt; None</span></p>

<p style="padding-left: 30px;">Set or stop the current music based on a string musictype.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_Gameplay_Functions">Gameplay Functions</a></p>

<p style="padding-left: 30px;">Current valid values for 'musictype': 'Menu', 'Victory', 'CharSelect',
'RunAway', 'Onslaught', 'Keep Away', 'Race', 'Epic Race', 'Scores',
'GrandRomp', 'ToTheDeath', 'Chosen One', 'ForwardMarch', 'FlagCatcher',
'Survival', 'Epic', 'Sports', 'Hockey', 'Football', 'Flying', 'Scary',
'Marching'.</p>

<p style="padding-left: 30px;">This function will handle loading and playing sound media as necessary,
and also supports custom user soundtracks on specific platforms so the
user can override particular game music with their own.</p>

<p style="padding-left: 30px;">Pass None to stop music.</p>

<p style="padding-left: 30px;">if 'continuous' is True the musictype passed is the same as what is already
playing, the playing track will not be restarted.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_sharedobj">ba.sharedobj()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">sharedobj(name: str) -&gt; Any</span></p>

<p style="padding-left: 30px;">Return a predefined object for the current Activity, creating if needed.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_Gameplay_Functions">Gameplay Functions</a></p>

<p style="padding-left: 30px;">Available values for 'name':</p>

<p style="padding-left: 30px;">'globals': returns the 'globals' <a href="#class_ba_Node">ba.Node</a>, containing various global
  controls & values.</p>

<p style="padding-left: 30px;">'object_material': a <a href="#class_ba_Material">ba.Material</a> that should be applied to any small,
  normal, physical objects such as bombs, boxes, players, etc. Other
  materials often check for the  presence of this material as a
  prerequisite for performing certain actions (such as disabling collisions
  between initially-overlapping objects)</p>

<p style="padding-left: 30px;">'player_material': a <a href="#class_ba_Material">ba.Material</a> to be applied to player parts.  Generally,
  materials related to the process of scoring when reaching a goal, etc
  will look for the presence of this material on things that hit them.</p>

<p style="padding-left: 30px;">'pickup_material': a <a href="#class_ba_Material">ba.Material</a>; collision shapes used for picking things
  up will have this material applied. To prevent an object from being
  picked up, you can add a material that disables collisions against things
  containing this material.</p>

<p style="padding-left: 30px;">'footing_material': anything that can be 'walked on' should have this
  <a href="#class_ba_Material">ba.Material</a> applied; generally just terrain and whatnot. A character will
  snap upright whenever touching something with this material so it should
  not be applied to props, etc.</p>

<p style="padding-left: 30px;">'attack_material': a <a href="#class_ba_Material">ba.Material</a> applied to explosion shapes, punch
  shapes, etc.  An object not wanting to receive impulse/etc messages can
  disable collisions against this material.</p>

<p style="padding-left: 30px;">'death_material': a <a href="#class_ba_Material">ba.Material</a> that sends a <a href="#class_ba_DieMessage">ba.DieMessage</a>() to anything
  that touches it; handy for terrain below a cliff, etc.</p>

<p style="padding-left: 30px;">'region_material':  a <a href="#class_ba_Material">ba.Material</a> used for non-physical collision shapes
  (regions); collisions can generally be allowed with this material even
  when initially overlapping since it is not physical.</p>

<p style="padding-left: 30px;">'railing_material': a <a href="#class_ba_Material">ba.Material</a> with a very low friction/stiffness/etc
  that can be applied to invisible 'railings' useful for gently keeping
  characters from falling off of cliffs.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_show_damage_count">ba.show_damage_count()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">show_damage_count(damage: str, position: Sequence[float], direction: Sequence[float]) -&gt; None</span></p>

<p style="padding-left: 30px;">Pop up a damage count at a position in space.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_textwidget">ba.textwidget()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">textwidget(edit: Widget = None, parent: Widget = None,
  size: Sequence[float] = None, position: Sequence[float] = None,
  text: Union[str, <a href="#class_ba_Lstr">ba.Lstr</a>] = None, v_align: str = None,
  h_align: str = None, editable: bool = None, padding: float = None,
  on_return_press_call: Callable[[], None] = None,
  on_activate_call: Callable[[], None] = None,
  selectable: bool = None, query: Widget = None, max_chars: int = None,
  color: Sequence[float] = None, click_activate: bool = None,
  on_select_call: Callable[[], None] = None,
  always_highlight: bool = None, draw_controller: Widget = None,
  scale: float = None, corner_scale: float = None,
  description: Union[str, <a href="#class_ba_Lstr">ba.Lstr</a>] = None,
  transition_delay: float = None, maxwidth: float = None,
  max_height: float = None, flatness: float = None,
  shadow: float = None, autoselect: bool = None, rotate: float = None,
  enabled: bool = None, force_internal_editing: bool = None,
  always_show_carat: bool = None, big: bool = None,
  extra_touch_border_scale: float = None, res_scale: float = None)
  -&gt; Widget</span></p>

<p style="padding-left: 30px;">Create or edit a text widget.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_User_Interface_Functions">User Interface Functions</a></p>

<p style="padding-left: 30px;">Pass a valid existing <a href="#class_ba_Widget">ba.Widget</a> as 'edit' to modify it; otherwise
a new one is created and returned. Arguments that are not set to None
are applied to the Widget.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_time">ba.time()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">time(timetype: <a href="#class_ba_TimeType">ba.TimeType</a> = TimeType.SIM,
  timeformat: <a href="#class_ba_TimeFormat">ba.TimeFormat</a> = TimeFormat.SECONDS)
  -&gt; Union[float, int]</span></p>

<p style="padding-left: 30px;">Return the current time.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p style="padding-left: 30px;">The time returned depends on the current <a href="#class_ba_Context">ba.Context</a> and timetype.</p>

<p style="padding-left: 30px;">timetype can be either SIM, BASE, or REAL. It defaults to
SIM. Types are explained below:</p>

<p style="padding-left: 30px;">SIM time maps to local simulation time in <a href="#class_ba_Activity">ba.Activity</a> or <a href="#class_ba_Session">ba.Session</a>
Contexts. This means that it may progress slower in slow-motion play
modes, stop when the game is paused, etc.  This time type is not
available in UI contexts.</p>

<p style="padding-left: 30px;">BASE time is also linked to gameplay in <a href="#class_ba_Activity">ba.Activity</a> or <a href="#class_ba_Session">ba.Session</a>
Contexts, but it progresses at a constant rate regardless of
 slow-motion states or pausing.  It can, however, slow down or stop
in certain cases such as network outages or game slowdowns due to
cpu load. Like 'sim' time, this is unavailable in UI contexts.</p>

<p style="padding-left: 30px;">REAL time always maps to actual clock time with a bit of filtering
added, regardless of Context.  (the filtering prevents it from going
backwards or jumping forward by large amounts due to the app being
backgrounded, system time changing, etc.)</p>

<p style="padding-left: 30px;">the 'timeformat' arg defaults to SECONDS which returns float seconds,
but it can also be MILLISECONDS to return integer milliseconds.</p>

<p style="padding-left: 30px;">Note: If you need pure unfiltered clock time, just use the standard
Python functions such as time.time().</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_timer">ba.timer()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">timer(time: float, call: Callable[[], Any], repeat: bool = False,
  timetype: <a href="#class_ba_TimeType">ba.TimeType</a> = TimeType.SIM,
  timeformat: <a href="#class_ba_TimeFormat">ba.TimeFormat</a> = TimeFormat.SECONDS,
  suppress_format_warning: bool = False)
 -&gt; None</span></p>

<p style="padding-left: 30px;">Schedule a call to run at a later point in time.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p style="padding-left: 30px;">This function adds a timer to the current <a href="#class_ba_Context">ba.Context</a>.
This timer cannot be canceled or modified once created. If you
 require the ability to do so, use the <a href="#class_ba_Timer">ba.Timer</a> class instead.</p>

<p style="padding-left: 30px;">time: length of time (in seconds by default) that the timer will wait
before firing. Note that the actual delay experienced may vary
 depending on the timetype. (see below)</p>

<p style="padding-left: 30px;">call: A callable Python object. Note that the timer will retain a
strong reference to the callable for as long as it exists, so you
may want to look into concepts such as <a href="#class_ba_WeakCall">ba.WeakCall</a> if that is not
desired.</p>

<p style="padding-left: 30px;">repeat: if True, the timer will fire repeatedly, with each successive
firing having the same delay as the first.</p>

<p style="padding-left: 30px;">timetype can be either 'sim', 'base', or 'real'. It defaults to
'sim'. Types are explained below:</p>

<p style="padding-left: 30px;">'sim' time maps to local simulation time in <a href="#class_ba_Activity">ba.Activity</a> or <a href="#class_ba_Session">ba.Session</a>
Contexts. This means that it may progress slower in slow-motion play
modes, stop when the game is paused, etc.  This time type is not
available in UI contexts.</p>

<p style="padding-left: 30px;">'base' time is also linked to gameplay in <a href="#class_ba_Activity">ba.Activity</a> or <a href="#class_ba_Session">ba.Session</a>
Contexts, but it progresses at a constant rate regardless of
 slow-motion states or pausing.  It can, however, slow down or stop
in certain cases such as network outages or game slowdowns due to
cpu load. Like 'sim' time, this is unavailable in UI contexts.</p>

<p style="padding-left: 30px;">'real' time always maps to actual clock time with a bit of filtering
added, regardless of Context.  (the filtering prevents it from going
backwards or jumping forward by large amounts due to the app being
backgrounded, system time changing, etc.)
Real time timers are currently only available in the UI context.</p>

<p style="padding-left: 30px;">the 'timeformat' arg defaults to seconds but can also be milliseconds.</p>

<pre style="padding-left: 30px;"><span style="color: #008800;"># timer example: print some stuff through time:</span>
<a href="#function_ba_screenmessage">ba.screenmessage</a>('hello from now!')
<a href="#function_ba_timer">ba.timer</a>(1.0, <a href="#class_ba_Call">ba.Call</a>(<a href="#function_ba_screenmessage">ba.screenmessage</a>, 'hello from the future!'))
<a href="#function_ba_timer">ba.timer</a>(2.0, <a href="#class_ba_Call">ba.Call</a>(<a href="#function_ba_screenmessage">ba.screenmessage</a>, 'hello from the future 2!'))</pre>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_timestring">ba.timestring()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">timestring(timeval: float, centi: bool = True, timeformat: <a href="#class_ba_TimeFormat">ba.TimeFormat</a> = &lt;TimeFormat.SECONDS: 0&gt;, suppress_format_warning: bool = False) -&gt; <a href="#class_ba_Lstr">ba.Lstr</a></span></p>

<p style="padding-left: 30px;">Generate a <a href="#class_ba_Lstr">ba.Lstr</a> for displaying a time value.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p style="padding-left: 30px;">Given a time value, returns a <a href="#class_ba_Lstr">ba.Lstr</a> with:
(hours if &gt; 0 ) : minutes : seconds : (centiseconds if centi=True).</p>

<p style="padding-left: 30px;">Time 'timeval' is specified in seconds by default, or 'timeformat' can
be set to <a href="#class_ba_TimeFormat">ba.TimeFormat</a>.MILLISECONDS to accept milliseconds instead.</p>

<p style="padding-left: 30px;">WARNING: the underlying Lstr value is somewhat large so don't use this
to rapidly update Node text values for an onscreen timer or you may
consume significant network bandwidth.  For that purpose you should
use a 'timedisplay' Node and attribute connections.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_uicleanupcheck">ba.uicleanupcheck()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">uicleanupcheck(obj: Any, widget: <a href="#class_ba_Widget">ba.Widget</a>) -&gt; None</span></p>

<p style="padding-left: 30px;">Add a check to ensure a widget-owning object gets cleaned up properly.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_User_Interface_Functions">User Interface Functions</a></p>

<p style="padding-left: 30px;">This adds a check which will print an error message if the provided
object still exists ~5 seconds after the provided <a href="#class_ba_Widget">ba.Widget</a> dies.</p>

<p style="padding-left: 30px;">This is a good sanity check for any sort of object that wraps or
controls a <a href="#class_ba_Widget">ba.Widget</a>. For instance, a 'Window' class instance has
no reason to still exist once its root container <a href="#class_ba_Widget">ba.Widget</a> has fully
transitioned out and been destroyed. Circular references or careless
strong referencing can lead to such objects never getting destroyed,
however, and this helps detect such cases to avoid memory leaks.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_vec3validate">ba.vec3validate()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">vec3validate(value: Sequence[float]) -&gt; Sequence[float]</span></p>

<p style="padding-left: 30px;">Ensure a value is valid for use as a Vec3.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_General_Utility_Functions">General Utility Functions</a></p>

<p style="padding-left: 30px;">Raises a TypeError exception if not.
Valid values include any type of sequence consisting of 3 numeric values.
Returns the same value as passed in (but with a definite type
so this can be used to disambiguate 'Any' types).
Generally this should be used in 'if __debug__' or assert clauses
to keep runtime overhead minimal.</p>

<hr>
<h2><strong><a class="offsanchor" name="function_ba_widget">ba.widget()</a></strong></h3>
<p style="padding-left: 80px; text-indent: -50px;"><span style="color: #666677;">widget(edit: <a href="#class_ba_Widget">ba.Widget</a> = None, up_widget: <a href="#class_ba_Widget">ba.Widget</a> = None,
  down_widget: <a href="#class_ba_Widget">ba.Widget</a> = None, left_widget: <a href="#class_ba_Widget">ba.Widget</a> = None,
  right_widget: <a href="#class_ba_Widget">ba.Widget</a> = None, show_buffer_top: float = None,
  show_buffer_bottom: float = None, show_buffer_left: float = None,
  show_buffer_right: float = None, autoselect: bool = None) -&gt; None</span></p>

<p style="padding-left: 30px;">Edit common attributes of any widget.</p>

<p style="padding-left: 30px;">Category: <a href="#function_category_User_Interface_Functions">User Interface Functions</a></p>

<p style="padding-left: 30px;">Unlike other UI calls, this can only be used to edit, not to create.</p>

