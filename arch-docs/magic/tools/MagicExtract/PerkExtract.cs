using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using MagicExtract.Projections;

namespace MagicExtract;

/// <summary>
/// Emits every perk the player can buy with Memory Points in the meditation space, as the
/// load-order-WINNING data says it is.
///
/// Enderal's memory trees are not the vanilla perk constellation (every AVIF PerkTree is empty).
/// The meditation power (_00E_Class_OpenClassMenuScript) teleports the player into cell
/// ClassMenue 0A7FBC:Skyrim.esm, where each "memory star" is a placed reference carrying
/// _00E_Class_PerkScript. That script's properties name the perk(s)/talent the star teaches and a
/// Message whose button CONDITIONS are the real purchase gate (prerequisite perks + TalentPoints).
/// So this walks: star REFR -> script properties -> Message buttons -> Perks / Shout.
/// Tree membership comes from the 11 *Perks FormLists _00E_Game_SkillmenuSC registers.
/// </summary>
public static class PerkExtract
{
    private const string PerkScript = "_00E_Class_PerkScript";
    private static readonly FormKey TalentPointsGlobal = FormKey.Factory("05BCFA:Skyrim.esm");

    // Registration order from _00E_Game_SkillmenuSC.InitAffinitySystem() [verified].
    private static readonly (int Index, string Code, string FormList, string NameMessageEdid, bool FsOnly)[] Trees =
    [
        (1, "Bastion", "06686B:Skyrim.esm", "_00E_Game_BastionName", false),
        (2, "Derwish", "06686D:Skyrim.esm", "_00E_Game_DerwishName", false),
        (3, "Elementalism", "066875:Skyrim.esm", "_00E_Game_ElementalismName", false),
        (4, "Espionage", "066889:Skyrim.esm", "_00E_Game_EspionageName", false),
        (5, "LifeAndDeath", "066873:Skyrim.esm", "_00E_Game_LifeAndDeathName", false),
        (6, "Manipulation", "06686A:Skyrim.esm", "_00E_Game_ManipulationName", false),
        (7, "Rage", "066887:Skyrim.esm", "_00E_Game_RageName", false),
        (8, "Trickery", "06687F:Skyrim.esm", "_00E_Game_TrickeryName", false),
        (9, "Vagabond", "066877:Skyrim.esm", "_00E_Game_VagabondName", false),
        (10, "Phasmalist", "044EEA:Skyrim.esm", "_00E_FS_Game_PhasmalistName", true),
        (11, "Theriantrophist", "02EE04:Enderal - Forgotten Stories.esm", "_00E_FS_Game_TheriantrophistName", true),
    ];

    public static bool Run(List<LoadedPlugin> loaded, ModlistLoadOrder lo, string profile, string outFile, List<string> warnings)
    {
        var perkChains = Chains.Build(loaded, m => m.Perks);
        var mesgChains = Chains.Build(loaded, m => m.Messages);
        var flstChains = Chains.Build(loaded, m => m.FormLists);
        var shouChains = Chains.Build(loaded, m => m.Shouts);
        var woopChains = Chains.Build(loaded, m => m.WordsOfPower);
        var actiChains = Chains.Build(loaded, m => m.Activators);
        var questChains = Chains.Build(loaded, m => m.Quests);

        var names = new NameIndex();
        names.Add(perkChains); names.Add(mesgChains); names.Add(shouChains);
        names.Add(woopChains); names.Add(actiChains); names.Add(questChains);

        // ---- star refs: every REFR anywhere whose VMAD carries the perk script ------------
        var refChains = new Dictionary<FormKey, List<(PluginEntry, IPlacedObjectGetter)>>();
        var refCell = new Dictionary<FormKey, ICellGetter>();
        foreach (var lp in loaded)
        {
            foreach (var (cell, r) in PlacedObjects(lp.Mod))
            {
                if (r.VirtualMachineAdapter?.Scripts.Any(s => s.Name.Equals(PerkScript, StringComparison.OrdinalIgnoreCase)) != true)
                    continue;
                if (!refChains.TryGetValue(r.FormKey, out var chain))
                    refChains[r.FormKey] = chain = new List<(PluginEntry, IPlacedObjectGetter)>(1);
                chain.Add((lp.Entry, r));
                refCell[r.FormKey] = cell;
            }
        }
        Console.WriteLine($"perks: {refChains.Count} memory-star refs carry {PerkScript}");

        // ---- trees --------------------------------------------------------------------------
        var winningMesgByEdid = mesgChains.Values.Select(c => c[^1].Item2)
            .Where(m => m.EditorID is not null)
            .GroupBy(m => m.EditorID!, StringComparer.OrdinalIgnoreCase)
            .ToDictionary(g => g.Key, g => g.Last(), StringComparer.OrdinalIgnoreCase);

        var perkToTree = new Dictionary<FormKey, string>();
        var treeDtos = new List<Dictionary<string, object?>>();
        foreach (var t in Trees)
        {
            var flk = FormKey.Factory(t.FormList);
            List<FormKey> members = new();
            ProvenanceLite? flProv = null;
            if (flstChains.TryGetValue(flk, out var flChain))
            {
                members = flChain[^1].Item2.Items.Select(i => i.FormKey).ToList();
                flProv = Prov(flChain);
            }
            else warnings.Add($"perks: tree FormList {flk} ({t.Code}) not found");
            foreach (var m in members) perkToTree.TryAdd(m, t.Code);

            string? display = null;
            if (winningMesgByEdid.TryGetValue(t.NameMessageEdid, out var nameMsg))
                display = Builders.Str(nameMsg.Description) ?? Builders.Str(nameMsg.Name);
            else warnings.Add($"perks: tree name message {t.NameMessageEdid} not found");

            treeDtos.Add(new Dictionary<string, object?>
            {
                ["index"] = t.Index,
                ["code"] = t.Code,
                ["displayName"] = display?.Trim(),
                ["forgottenStoriesOnly"] = t.FsOnly,
                ["perkFormList"] = new { formKey = t.FormList, provenance = flProv },
                ["perkFormListSize"] = members.Count,
            });
        }
        // Not a registered tree: the three class-root talent stars (_00E_Class_Root*). Their perks
        // sit in no *Perks FormList, so they count toward no tree and unlock no affinity.
        treeDtos.Insert(0, new Dictionary<string, object?>
        {
            ["index"] = 0,
            ["code"] = "root",
            ["displayName"] = "Class roots (warrior / mage / rogue starting talents)",
            ["forgottenStoriesOnly"] = false,
            ["perkFormList"] = null,
            ["perkFormListSize"] = 0,
        });

        // ---- stars --------------------------------------------------------------------------
        var stars = new List<Dictionary<string, object?>>();
        var inert = new List<object>();
        var taughtPerks = new HashSet<FormKey>();
        int skippedDeleted = 0;
        foreach (var (fk, chain) in refChains.OrderBy(kv => kv.Key.ModKey.FileName.String).ThenBy(kv => kv.Key.ID))
        {
            var r = chain[^1].Item2;
            if (r.IsDeleted) { skippedDeleted++; continue; }
            var script = r.VirtualMachineAdapter!.Scripts.FirstOrDefault(s => s.Name.Equals(PerkScript, StringComparison.OrdinalIgnoreCase));
            if (script is null) { warnings.Add($"perks: winning {fk} dropped {PerkScript}"); continue; }
            // Refs carry the script with Flags: Inherited — the base Activator's properties apply
            // unless the REFR sets the same property. Base first, then the ref overlays it.
            var props = new Dictionary<string, IScriptPropertyGetter>(StringComparer.OrdinalIgnoreCase);
            var baseActi = actiChains.GetValueOrDefault(r.Base.FormKey)?[^1].Item2;
            var baseScript = baseActi?.VirtualMachineAdapter?.Scripts
                .FirstOrDefault(s => s.Name.Equals(PerkScript, StringComparison.OrdinalIgnoreCase));
            if (baseScript is not null) foreach (var p in baseScript.Properties) props[p.Name] = p;
            int inheritedCount = props.Count;
            foreach (var p in script.Properties) props[p.Name] = p;

            FormKey Obj(string n) => props.TryGetValue(n, out var p) && p is IScriptObjectPropertyGetter o ? o.Object.FormKey : FormKey.Null;
            bool Bool(string n) => props.TryGetValue(n, out var p) && p is IScriptBoolPropertyGetter b && b.Data;
            float? Flt(string n) => props.TryGetValue(n, out var p) && p is IScriptFloatPropertyGetter f ? f.Data : null;

            var rankPerks = new[] { Obj("__Config_PerkToTeach1"), Obj("__Config_PerkToTeach2"), Obj("__Config_PerkToTeach3") };
            bool multi = Bool("__Config_MultipleLevels") || Bool("__Config_MultipleLevelsConfirm");
            bool twoLevels = Bool("__Config_MultipleLevelsTwoLevels");
            bool teachesTalent = Bool("__Config_TeachesTalent");
            // Mirrors OnActivate: multi-level stars teach 2 or 3 ranks, single stars only rank 1.
            int rankCount = !multi ? 1 : twoLevels ? 2 : 3;
            var ownPerks = rankPerks.Take(rankCount).Where(p => !p.IsNull).ToHashSet();
            var additional = Obj("AdditionalPerk");
            foreach (var p in ownPerks) taughtPerks.Add(p);
            if (!additional.IsNull) taughtPerks.Add(additional);

            var msgKey = Obj("__Config_DisplayMessage");
            IMessageGetter? msg = null;
            ProvenanceLite? msgProv = null;
            if (!msgKey.IsNull && mesgChains.TryGetValue(msgKey, out var mChain)) { msg = mChain[^1].Item2; msgProv = Prov(mChain); }
            else warnings.Add($"perks: star {fk} message {msgKey} not resolved");

            // tree: by rank-1 perk's FormList membership, else any own perk
            string? tree = ownPerks.Select(p => perkToTree.GetValueOrDefault(p)).FirstOrDefault(x => x is not null);
            string? treeSource = tree is null ? null : "perkFormList";
            if (tree is null)
            {
                // The perk isn't in any *Perks FormList, so buying it does NOT count toward the
                // tree's points/affinities — but the star still sits in that tree visually.
                tree = TreeFromEditorId(baseActi?.EditorID) ?? TreeFromEditorId(msg?.EditorID);
                treeSource = tree is null ? null : "editorIdFallback";
                warnings.Add($"perks: star {fk} ({msg?.EditorID ?? baseActi?.EditorID}) teaches no perk in any tree FormList" +
                             (tree is null ? "" : $"; placed in {tree} by EditorID"));
            }

            // buttons -> ranks. In OnActivate the button INDEX picks the action: buttons below
            // rankCount (or button 0 for single stars) unlock; the rest are info/cancel.
            var buttons = new List<Dictionary<string, object?>>();
            var ranks = new List<Dictionary<string, object?>>();
            if (msg is not null)
            {
                for (int bi = 0; bi < msg.MenuButtons.Count; bi++)
                {
                    var b = msg.MenuButtons[bi];
                    bool unlocks = bi < rankCount;
                    var req = Requirements(b.Conditions, ownPerks, names);
                    buttons.Add(new Dictionary<string, object?>
                    {
                        ["index"] = bi,
                        ["text"] = Builders.Str(b.Text)?.Trim(),
                        ["unlocks"] = unlocks,
                        ["conditions"] = Builders.Conditions(b.Conditions),
                    });
                    if (!unlocks) continue;
                    // For a talent the button rank maps onto perk rank (TeachTalent adds perk 2/3);
                    // TeachPerk always picks the lowest perk not yet owned, independent of button.
                    var perkFk = rankPerks[bi];
                    ranks.Add(new Dictionary<string, object?>
                    {
                        ["rank"] = bi + 1,
                        ["buttonText"] = Builders.Str(b.Text)?.Trim(),
                        ["perk"] = perkFk.IsNull ? null : PerkInfo(perkFk, perkChains),
                        // GetPerkDistribution only counts perks in the WINNING *Perks FormList.
                        ["inTreeFormList"] = !perkFk.IsNull && perkToTree.ContainsKey(perkFk),
                        ["memoryPointCost"] = req.Cost,
                        ["requiresAllOf"] = req.AllOf.Count == 0 ? null : req.AllOf,
                        ["requiresAnyOf"] = req.AnyOf.Count == 0 ? null : req.AnyOf,
                        ["otherConditions"] = req.Other.Count == 0 ? null : req.Other,
                    });
                }
            }

            // prerequisites of the star itself = rank-1 requirements on perks outside the star
            object? prerequisites = ranks.Count > 0 ? new
            {
                allOf = ranks[0]["requiresAllOf"],
                anyOf = ranks[0]["requiresAnyOf"],
            } : null;

            Dictionary<string, object?>? talent = null;
            if (teachesTalent)
            {
                var shoutFk = Obj("__Config_TalentToTeach");
                var words = new[] { Obj("__Config_WordToTeach1"), Obj("__Config_WordToTeach2"), Obj("__Config_WordToTeach3") };
                IShoutGetter? shout = shoutFk.IsNull ? null : shouChains.GetValueOrDefault(shoutFk)?[^1].Item2;
                talent = new Dictionary<string, object?>
                {
                    ["shout"] = names.Ref(new FormLinkInformation(shoutFk, typeof(IShoutGetter))),
                    ["shoutDescription"] = Builders.Str(shout?.Description),
                    ["words"] = words.Where(w => !w.IsNull).Select(w => names.Ref(new FormLinkInformation(w, typeof(IWordOfPowerGetter)))).ToList(),
                    ["wordRecoveryTimes"] = shout?.WordsOfPower.Select(w => w.RecoveryTime).ToList(),
                    ["scriptRecoveryTimeRank2"] = Flt("fRecoveryTime02"),
                    ["scriptRecoveryTimeRank3"] = Flt("fRecoveryTime03"),
                    ["provenance"] = shoutFk.IsNull ? null : Prov(shouChains.GetValueOrDefault(shoutFk)),
                };
            }

            if (msgKey.IsNull && ownPerks.Count == 0)
            {
                // Neither the ref nor its base sets anything: activating it shows no message box.
                inert.Add(new { refFormKey = fk.ToString(), @base = names.Ref(r.Base), provenance = Prov(chain) });
                continue;
            }

            var quest = Obj("__Config_QuestToStart");
            var en = r.EnableParent;
            stars.Add(new Dictionary<string, object?>
            {
                ["name"] = Builders.Str(msg?.Name)?.Trim()
                           ?? names.Ref(new FormLinkInformation(r.Base.FormKey, typeof(IActivatorGetter)))?.Name,
                ["nameInBaseEnderal"] = BaseName(msgKey, mesgChains, Builders.Str(msg?.Name)?.Trim()),
                ["tree"] = tree,
                ["treeSource"] = treeSource,
                ["countsTowardTreePoints"] = treeSource == "perkFormList", // per rank: rankDetails[].inTreeFormList
                ["kind"] = teachesTalent ? "talent" : rankCount > 1 ? "rankedPerk" : "perk",
                ["ranks"] = rankCount,
                ["description"] = Builders.Str(msg?.Description)?.Trim(),
                ["prerequisites"] = prerequisites,
                ["rankDetails"] = ranks,
                ["talent"] = talent,
                ["additionalPerk"] = additional.IsNull ? null : PerkInfo(additional, perkChains),
                ["questStartedOnUnlock"] = names.Ref(new FormLinkInformation(quest, typeof(IQuestGetter))),
                ["message"] = new { formKey = msgKey.IsNull ? null : msgKey.ToString(), editorId = msg?.EditorID, provenance = msgProv },
                ["messageButtons"] = buttons,
                ["star"] = new Dictionary<string, object?>
                {
                    ["refFormKey"] = fk.ToString(),
                    ["base"] = names.Ref(r.Base),
                    ["propertiesInheritedFromBase"] = inheritedCount,
                    ["cell"] = refCell.TryGetValue(fk, out var cl) ? $"{cl.EditorID} {cl.FormKey}" : null,
                    ["position"] = r.Placement is null ? null : new[] { r.Placement.Position.X, r.Placement.Position.Y, r.Placement.Position.Z },
                    ["initiallyDisabled"] = (r.MajorRecordFlagsRaw & 0x800) != 0,
                    ["enableParent"] = en is null ? null : new { reference = en.Reference.FormKey.ToString(), flags = en.Flags.ToString() },
                    ["provenance"] = Prov(chain),
                },
            });
        }

        // ---- orphans: perks in tree FormLists no star teaches (and vice versa) ----------
        var orphans = perkToTree.Keys.Where(p => !taughtPerks.Contains(p))
            .Select(p => new { tree = perkToTree[p], perk = PerkInfo(p, perkChains) }).ToList();

        var ordered = stars
            .OrderBy(s => (string?)s["tree"] == "root" ? -1 : Array.FindIndex(Trees, t => t.Code == (string?)s["tree"]) is var i && i < 0 ? 99 : i)
            .ThenBy(s => (string?)s["name"], StringComparer.Ordinal).ToList();

        var payload = new Dictionary<string, object?>
        {
            ["schemaVersion"] = 1,
            ["generatedBy"] = "MagicExtract --perks (Mutagen.Bethesda.Skyrim 0.54.4, read-only)",
            ["extractedAt"] = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"),
            ["profile"] = profile,
            ["source"] = "memory-star REFRs carrying _00E_Class_PerkScript (meditation cell ClassMenue 0A7FBC:Skyrim.esm), load-order winners",
            ["counts"] = new Dictionary<string, int>
            {
                ["stars"] = ordered.Count,
                ["talents"] = ordered.Count(s => (string?)s["kind"] == "talent"),
                ["rankedPerks"] = ordered.Count(s => (string?)s["kind"] == "rankedPerk"),
                ["singlePerks"] = ordered.Count(s => (string?)s["kind"] == "perk"),
                ["totalMemoryPointsToMaxEverything"] = ordered.Sum(s => (int)s["ranks"]!),
                ["deletedStarsSkipped"] = skippedDeleted,
                ["inertStars"] = inert.Count,
                ["treePerksWithNoStar"] = orphans.Count,
            },
            ["trees"] = treeDtos,
            ["perks"] = ordered,
            ["inertStars"] = inert,
            ["treePerksWithNoStar"] = orphans,
        };
        Json.WriteFile(outFile, payload);
        Console.WriteLine($"perks: wrote {ordered.Count} stars ({ordered.Sum(s => (int)s["ranks"]!)} ranks) -> {outFile}");

        bool ok = true;
        if (ordered.Count < 150) { Console.Error.WriteLine($"FATAL: only {ordered.Count} stars found; base Enderal + FS place 170"); ok = false; }
        if (ordered.Any(s => s["tree"] is null)) warnings.Add("perks: some stars have no tree (see warnings above)");
        return ok;
    }

    // ---- helpers ----------------------------------------------------------------------------

    private static readonly (string Token, string Tree)[] TreeTokens =
    [
        ("Keeper", "Bastion"), ("Bastion", "Bastion"), ("Bladedancer", "Derwish"), ("Derwish", "Derwish"),
        ("Elementalist", "Elementalism"), ("Infiltrator", "Espionage"), ("Sinistrope", "LifeAndDeath"),
        ("Thaumaturge", "Manipulation"), ("Vandal", "Rage"), ("Trickster", "Trickery"),
        ("Vagrant", "Vagabond"), ("Vagabond", "Vagabond"), ("Phasmalist", "Phasmalist"),
        ("Theriantrophist", "Theriantrophist"), ("Lycanthrop", "Theriantrophist"),
        ("_Class_Root", "root"),
    ];

    private static string? TreeFromEditorId(string? edid)
        => edid is null ? null : TreeTokens.FirstOrDefault(t => edid.Contains(t.Token, StringComparison.OrdinalIgnoreCase)).Tree;

    /// <summary>The defining master's title, when a later plugin changed it (EGO ships German ones).</summary>
    private static string? BaseName(FormKey msgKey, Dictionary<FormKey, List<(PluginEntry, IMessageGetter)>> chains, string? winning)
    {
        if (msgKey.IsNull || !chains.TryGetValue(msgKey, out var c)) return null;
        var first = Builders.Str(c[0].Item2.Name)?.Trim();
        return first == winning ? null : first;
    }

    private sealed record ProvenanceLite(string DefinedIn, string Winner, List<string> Chain);

    private static ProvenanceLite? Prov<T>(List<(PluginEntry, T)>? chain)
        => chain is null || chain.Count == 0 ? null
            : new ProvenanceLite(chain[0].Item1.Name, chain[^1].Item1.Name, chain.Select(c => c.Item1.Name).ToList());

    private static object PerkInfo(FormKey fk, Dictionary<FormKey, List<(PluginEntry, IPerkGetter)>> perkChains)
    {
        if (!perkChains.TryGetValue(fk, out var chain))
            return new { formKey = fk.ToString(), missing = true };
        var p = chain[^1].Item2;
        return new
        {
            formKey = fk.ToString(),
            editorId = p.EditorID,
            name = Builders.Str(p.Name),
            description = Builders.Str(p.Description)?.Trim(),
            playable = p.Playable,
            hidden = p.Hidden,
            effectCount = p.Effects.Count,
            provenance = Prov(chain),
        };
    }

    private sealed class Req
    {
        public int? Cost;
        public List<object> AllOf = new();
        public List<List<object>> AnyOf = new();
        public List<object> Other = new();
    }

    /// <summary>
    /// Splits a button's condition list into: Memory Point cost, required perks, and the rest.
    /// Conditions with the OR flag chain with the NEXT condition (Bethesda semantics: OR binds
    /// tighter than AND), so consecutive OR'd HasPerk==1 checks become one anyOf group.
    /// HasPerk == 0 on the star's own rank perks is just rank ordering and is dropped.
    /// </summary>
    private static Req Requirements(IReadOnlyList<IConditionGetter> conds, HashSet<FormKey> own, NameIndex names)
    {
        var req = new Req();
        var group = new List<IConditionGetter>();
        void Flush()
        {
            if (group.Count == 0) return;
            var reqPerks = new List<object>();
            bool allHasPerk = true;
            foreach (var c in group)
            {
                if (c.Data is IHasPerkConditionDataGetter hp && c is IConditionFloatGetter f
                    && c.CompareOperator == CompareOperator.EqualTo && f.ComparisonValue == 1)
                    reqPerks.Add(names.Ref(hp.Perk.Link)!);
                else allHasPerk = false;
            }
            if (group.Count == 1 && reqPerks.Count == 1) req.AllOf.Add(reqPerks[0]);
            else if (allHasPerk) req.AnyOf.Add(reqPerks);
            else foreach (var c in group) Other(c);
            group.Clear();
        }
        void Other(IConditionGetter c)
        {
            if (c.Data is IGetGlobalValueConditionDataGetter g && g.Global.Link.FormKey == TalentPointsGlobal
                && c is IConditionFloatGetter gf)
            { req.Cost = (int)gf.ComparisonValue; return; }
            if (c.Data is IHasPerkConditionDataGetter hp && c is IConditionFloatGetter f
                && f.ComparisonValue == 0 && own.Contains(hp.Perk.Link.FormKey))
                return; // rank ordering on the star's own perks
            if (c.Data is IHasPerkConditionDataGetter hp2 && c is IConditionFloatGetter f2 && f2.ComparisonValue == 0)
            { req.Other.Add(new { lacksPerk = names.Ref(hp2.Perk.Link) }); return; }
            req.Other.Add(Builders.Conditions(new[] { c })![0]);
        }
        foreach (var c in conds)
        {
            bool isPerkReq = c.Data is IHasPerkConditionDataGetter && c is IConditionFloatGetter ff && ff.ComparisonValue == 1
                             && c.CompareOperator == CompareOperator.EqualTo;
            if (!isPerkReq && group.Count == 0) { Other(c); continue; }
            group.Add(c);
            if (!c.Flags.HasFlag(Condition.Flag.OR)) Flush();
        }
        Flush();
        return req;
    }

    /// <summary>Every placed object with its owning cell (interior + exterior, persistent + temporary).</summary>
    private static IEnumerable<(ICellGetter, IPlacedObjectGetter)> PlacedObjects(ISkyrimModGetter mod)
    {
        IEnumerable<ICellGetter> Cells()
        {
            foreach (var blk in mod.Cells)
                foreach (var sub in blk.SubBlocks)
                    foreach (var c in sub.Cells) yield return c;
            foreach (var ws in mod.Worldspaces)
            {
                if (ws.TopCell is not null) yield return ws.TopCell;
                foreach (var blk in ws.SubCells)
                    foreach (var sub in blk.Items)
                        foreach (var c in sub.Items) yield return c;
            }
        }
        foreach (var c in Cells())
            foreach (var r in c.Persistent.Concat(c.Temporary))
                if (r is IPlacedObjectGetter po) yield return (c, po);
    }
}
