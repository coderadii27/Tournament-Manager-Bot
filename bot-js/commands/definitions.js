import { SlashCommandBuilder, PermissionFlagsBits } from "discord.js";

export function buildSlashDefinitions() {
  const cmds = [];

  // Moderation
  cmds.push(new SlashCommandBuilder().setName("ban").setDescription("Ban a user.")
    .addUserOption(o => o.setName("user").setDescription("User").setRequired(true))
    .addStringOption(o => o.setName("reason").setDescription("Reason"))
    .setDefaultMemberPermissions(PermissionFlagsBits.BanMembers).toJSON());

  cmds.push(new SlashCommandBuilder().setName("kick").setDescription("Kick a user.")
    .addUserOption(o => o.setName("user").setDescription("User").setRequired(true))
    .addStringOption(o => o.setName("reason").setDescription("Reason"))
    .setDefaultMemberPermissions(PermissionFlagsBits.KickMembers).toJSON());

  cmds.push(new SlashCommandBuilder().setName("mute").setDescription("Timeout a user. e.g. 10m, 2h, 1d.")
    .addUserOption(o => o.setName("user").setDescription("User").setRequired(true))
    .addStringOption(o => o.setName("time").setDescription("Duration (10m, 2h, 1d)").setRequired(true))
    .addStringOption(o => o.setName("reason").setDescription("Reason"))
    .setDefaultMemberPermissions(PermissionFlagsBits.ModerateMembers).toJSON());

  cmds.push(new SlashCommandBuilder().setName("unmute").setDescription("Remove timeout.")
    .addUserOption(o => o.setName("user").setDescription("User").setRequired(true))
    .setDefaultMemberPermissions(PermissionFlagsBits.ModerateMembers).toJSON());

  // Tournament info / settings
  cmds.push(new SlashCommandBuilder().setName("info").setDescription("Show tournament info.").toJSON());

  cmds.push(new SlashCommandBuilder().setName("teamlist").setDescription("Show all confirmed teams.").toJSON());

  cmds.push(new SlashCommandBuilder().setName("setslots").setDescription("Update total tournament slots.")
    .addIntegerOption(o => o.setName("slots").setDescription("Total slots").setMinValue(2).setMaxValue(256).setRequired(true))
    .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild).toJSON());

  cmds.push(new SlashCommandBuilder().setName("setteamsize").setDescription("Update players per team.")
    .addIntegerOption(o => o.setName("size").setDescription("Players per team").setMinValue(1).setMaxValue(10).setRequired(true))
    .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild).toJSON());

  cmds.push(new SlashCommandBuilder().setName("settournamentname").setDescription("Rename tournament.")
    .addStringOption(o => o.setName("name").setDescription("New name").setRequired(true))
    .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild).toJSON());

  cmds.push(new SlashCommandBuilder().setName("endtournament").setDescription("End and reset the tournament.")
    .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild).toJSON());

  cmds.push(new SlashCommandBuilder().setName("removeteam").setDescription("Remove a team by name.")
    .addStringOption(o => o.setName("team").setDescription("Team name").setRequired(true))
    .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild).toJSON());

  cmds.push(new SlashCommandBuilder().setName("lineup").setDescription("Show group lineup.").toJSON());

  // Schedule
  cmds.push(new SlashCommandBuilder().setName("addmatch").setDescription("Add/update a match.")
    .addIntegerOption(o => o.setName("match_no").setDescription("Match number").setRequired(true))
    .addStringOption(o => o.setName("team_a").setDescription("Team A").setRequired(true))
    .addStringOption(o => o.setName("team_b").setDescription("Team B"))
    .addStringOption(o => o.setName("time").setDescription("When"))
    .addStringOption(o => o.setName("room_id").setDescription("Room ID"))
    .addStringOption(o => o.setName("room_pass").setDescription("Room password"))
    .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild).toJSON());

  cmds.push(new SlashCommandBuilder().setName("removematch").setDescription("Remove a match.")
    .addIntegerOption(o => o.setName("match_no").setDescription("Match number").setRequired(true))
    .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild).toJSON());

  cmds.push(new SlashCommandBuilder().setName("schedule").setDescription("Show match schedule.").toJSON());

  cmds.push(new SlashCommandBuilder().setName("idp").setDescription("Send IDP for a match.")
    .addIntegerOption(o => o.setName("match_no").setDescription("Match number").setRequired(true))
    .addStringOption(o => o.setName("room_id").setDescription("Room ID").setRequired(true))
    .addStringOption(o => o.setName("room_pass").setDescription("Room password").setRequired(true))
    .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild).toJSON());

  // Points
  cmds.push(new SlashCommandBuilder().setName("setpoints").setDescription("Set points for a team.")
    .addStringOption(o => o.setName("team").setDescription("Team name").setRequired(true))
    .addIntegerOption(o => o.setName("points").setDescription("Points").setRequired(true))
    .addIntegerOption(o => o.setName("kills").setDescription("Kills"))
    .addIntegerOption(o => o.setName("wins").setDescription("Wins"))
    .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild).toJSON());

  cmds.push(new SlashCommandBuilder().setName("addpoints").setDescription("Add to team points.")
    .addStringOption(o => o.setName("team").setDescription("Team name").setRequired(true))
    .addIntegerOption(o => o.setName("points").setDescription("Points to add"))
    .addIntegerOption(o => o.setName("kills").setDescription("Kills to add"))
    .addIntegerOption(o => o.setName("wins").setDescription("Wins to add"))
    .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild).toJSON());

  cmds.push(new SlashCommandBuilder().setName("resetpoints").setDescription("Reset point table.")
    .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild).toJSON());

  cmds.push(new SlashCommandBuilder().setName("points").setDescription("Show point table.").toJSON());

  // Communication
  cmds.push(new SlashCommandBuilder().setName("announce").setDescription("Multi-line announcement form.")
    .addBooleanOption(o => o.setName("ping_everyone").setDescription("Ping @everyone?"))
    .addStringOption(o => o.setName("image_url").setDescription("Banner image URL"))
    .setDefaultMemberPermissions(PermissionFlagsBits.ManageMessages).toJSON());

  cmds.push(new SlashCommandBuilder().setName("dmcaptains").setDescription("DM all team captains (form).")
    .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild).toJSON());

  cmds.push(new SlashCommandBuilder().setName("greet").setDescription("DM a welcome message + image to all members.")
    .addStringOption(o => o.setName("image_url").setDescription("Banner image URL"))
    .addStringOption(o => o.setName("footer_gif").setDescription("Footer icon/GIF URL"))
    .addRoleOption(o => o.setName("role").setDescription("Only DM members with this role"))
    .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild).toJSON());

  cmds.push(new SlashCommandBuilder().setName("sayembed").setDescription("Build a custom embed.")
    .addStringOption(o => o.setName("color_hex").setDescription("Hex color e.g. #9B5CF6"))
    .addStringOption(o => o.setName("image_url").setDescription("Banner image URL"))
    .addStringOption(o => o.setName("thumbnail_url").setDescription("Thumbnail URL"))
    .addStringOption(o => o.setName("footer_icon_url").setDescription("Footer icon/GIF URL"))
    .setDefaultMemberPermissions(PermissionFlagsBits.ManageMessages).toJSON());

  cmds.push(new SlashCommandBuilder().setName("poll").setDescription("Quick poll (up to 5 options).")
    .addStringOption(o => o.setName("question").setDescription("Question").setRequired(true))
    .addStringOption(o => o.setName("option1").setDescription("Option 1"))
    .addStringOption(o => o.setName("option2").setDescription("Option 2"))
    .addStringOption(o => o.setName("option3").setDescription("Option 3"))
    .addStringOption(o => o.setName("option4").setDescription("Option 4"))
    .addStringOption(o => o.setName("option5").setDescription("Option 5")).toJSON());

  cmds.push(new SlashCommandBuilder().setName("serverinfo").setDescription("Server info.").toJSON());
  cmds.push(new SlashCommandBuilder().setName("userinfo").setDescription("User info.")
    .addUserOption(o => o.setName("user").setDescription("User")).toJSON());
  cmds.push(new SlashCommandBuilder().setName("avatar").setDescription("Show user avatar.")
    .addUserOption(o => o.setName("user").setDescription("User")).toJSON());

  // Welcome system
  cmds.push(new SlashCommandBuilder().setName("setwelcome").setDescription("Set the welcome channel + message.")
    .addChannelOption(o => o.setName("channel").setDescription("Channel").setRequired(true))
    .addStringOption(o => o.setName("message").setDescription("Welcome text. Use {user}, {server}.").setRequired(true))
    .addStringOption(o => o.setName("image_url").setDescription("Banner image URL"))
    .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild).toJSON());

  cmds.push(new SlashCommandBuilder().setName("welcomeoff").setDescription("Disable auto-welcome.")
    .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild).toJSON());

  cmds.push(new SlashCommandBuilder().setName("help").setDescription("Show all commands.").toJSON());

  // Tickets
  cmds.push(new SlashCommandBuilder().setName("ticketsetup").setDescription("Configure ticket system & post the panel.")
    .addRoleOption(o => o.setName("staff_role").setDescription("Role that can see, claim and close tickets"))
    .addChannelOption(o => o.setName("category").setDescription("Category to host new tickets").addChannelTypes(4))
    .addChannelOption(o => o.setName("channel").setDescription("Channel to post the panel in").addChannelTypes(0))
    .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild).toJSON());

  cmds.push(new SlashCommandBuilder().setName("ticketpanel").setDescription("Re-post the ticket panel here.")
    .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild).toJSON());

  cmds.push(new SlashCommandBuilder().setName("ticketclose").setDescription("Close the current ticket channel.").toJSON());

  return cmds;
}
