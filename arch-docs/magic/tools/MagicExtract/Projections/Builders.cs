using System.Reflection;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Aspects;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Strings;

namespace MagicExtract.Projections;

/// <summary>FormKey → (EditorID, Name) of the WINNING record, for decorating references.</summary>
public sealed class NameIndex
{
    private readonly Dictionary<FormKey, (string? EditorId, string? Name)> _map = new();

    public void Add<T>(Dictionary<FormKey, List<(PluginEntry, T)>> chains)
        where T : class, ISkyrimMajorRecordGetter
    {
        foreach (var (fk, chain) in chains)
        {
            var win = chain[^1].Item2;
            string? name = win is INamedGetter n ? n.Name : null;
            _map[fk] = (win.EditorID, name);
        }
    }

    public RefDto? Ref(IFormLinkIdentifier? link)
    {
        if (link is null || link.FormKey.IsNull) return null;
        var dto = new RefDto { FormKey = link.FormKey.ToString() };
        if (_map.TryGetValue(link.FormKey, out var v)) { dto.EditorId = v.EditorId; dto.Name = v.Name; }
        return dto;
    }

    public string? Key(IFormLinkIdentifier? link)
        => link is null || link.FormKey.IsNull ? null : link.FormKey.ToString();
}

public static class Builders
{
    public static string? Str(ITranslatedStringGetter? s)
    {
        var v = s?.String;
        return string.IsNullOrEmpty(v) ? null : v;
    }

    // ---- conditions ------------------------------------------------------------------

    private static readonly HashSet<string> SkippedConditionProps =
        ["RunOnType", "Reference", "Unknown3", "UseAliases", "UsePackageData", "StaticRegistration"];

    public static List<ConditionDto>? Conditions(IReadOnlyList<IConditionGetter>? conds)
    {
        if (conds is null || conds.Count == 0) return null;
        var list = new List<ConditionDto>(conds.Count);
        foreach (var c in conds)
        {
            var data = c.Data;
            var dto = new ConditionDto
            {
                Function = data.GetType().Name.Replace("ConditionData", ""),
                RunOn = data.RunOnType.ToString(),
                Reference = data.Reference.FormKey.IsNull ? null : data.Reference.FormKey.ToString(),
                Operator = c.CompareOperator.ToString(),
                Or = c.Flags.HasFlag(Condition.Flag.OR),
            };
            switch (c)
            {
                case IConditionFloatGetter f: dto.Value = f.ComparisonValue; break;
                case IConditionGlobalGetter g: dto.Value = g.ComparisonValue.FormKey.ToString(); break;
            }
            // Function parameters vary per ConditionData subclass; reflect the interesting ones.
            Dictionary<string, string>? ps = null;
            foreach (var prop in data.GetType().GetProperties(BindingFlags.Public | BindingFlags.Instance))
            {
                if (SkippedConditionProps.Contains(prop.Name)) continue;
                if (prop.GetIndexParameters().Length > 0) continue;
                object? val;
                try { val = prop.GetValue(data); } catch { continue; }
                var rendered = RenderParam(val);
                if (rendered is null) continue;
                (ps ??= new Dictionary<string, string>())[prop.Name] = rendered;
            }
            dto.Parameters = ps;
            list.Add(dto);
        }
        return list;
    }

    private static string? RenderParam(object? val)
    {
        switch (val)
        {
            case null: return null;
            case IFormLinkIdentifier fli:
                return fli.FormKey.IsNull ? null : fli.FormKey.ToString();
            case string s: return s.Length == 0 ? null : s;
            case bool b: return b ? "true" : null; // default-false noise suppressed
            case Enum e: return e.ToString();
            case float or double or int or uint or short or ushort or byte or sbyte or long or ulong:
                return Convert.ToString(val, System.Globalization.CultureInfo.InvariantCulture);
        }
        // FormLinkOrIndex and friends expose a nested Link.
        var linkProp = val.GetType().GetProperty("Link");
        if (linkProp?.GetValue(val) is IFormLinkIdentifier nested && !nested.FormKey.IsNull)
            return nested.FormKey.ToString();
        return null;
    }

    // ---- effects ------------------------------------------------------------------------

    public static List<EffectDto>? Effects(IReadOnlyList<IEffectGetter>? effects, NameIndex names,
        IReadOnlyDictionary<FormKey, IMagicEffectGetter> winningMgef)
    {
        if (effects is null || effects.Count == 0) return null;
        var list = new List<EffectDto>(effects.Count);
        for (int i = 0; i < effects.Count; i++)
        {
            var e = effects[i];
            var dto = new EffectDto
            {
                Index = i,
                BaseEffect = names.Ref(e.BaseEffect),
                Magnitude = e.Data?.Magnitude ?? 0,
                Area = e.Data?.Area ?? 0,
                Duration = e.Data?.Duration ?? 0,
                Conditions = Conditions(e.Conditions),
            };
            if (winningMgef.TryGetValue(e.BaseEffect.FormKey, out var mgef))
            {
                dto.EffectCost = CostCalculator.EffectCost(mgef, dto.Magnitude, dto.Duration);
                dto.Archetype = mgef.Archetype.Type.ToString();
                var av = mgef.Archetype.ActorValue;
                dto.ActorValue = av == ActorValue.None ? null : av.ToString();
            }
            list.Add(dto);
        }
        return list;
    }

    public static List<RefDto>? Keywords(IReadOnlyList<IFormLinkGetter<IKeywordGetter>>? kws, NameIndex names)
    {
        if (kws is null || kws.Count == 0) return null;
        var list = new List<RefDto>(kws.Count);
        foreach (var k in kws)
            if (names.Ref(k) is { } r) list.Add(r);
        return list.Count == 0 ? null : list;
    }

    public static List<string>? FlagList<TEnum>(TEnum flags) where TEnum : struct, Enum
    {
        var list = new List<string>();
        foreach (var f in Enum.GetValues<TEnum>())
        {
            if (Convert.ToUInt64(f) == 0) continue;
            if (flags.HasFlag(f)) list.Add(f.ToString());
        }
        return list.Count == 0 ? null : list;
    }

    // ---- record projections ---------------------------------------------------------------

    public static SpellDto Spell(ISpellGetter s, NameIndex names,
        IReadOnlyDictionary<FormKey, IMagicEffectGetter> winningMgef,
        IReadOnlyDictionary<ActorValue, string> schoolNames)
    {
        var dto = new SpellDto
        {
            FormKey = s.FormKey.ToString(),
            EditorId = s.EditorID,
            Name = Str(s.Name),
            Description = Str(s.Description),
            Type = s.Type.ToString(),
            CastType = s.CastType.ToString(),
            TargetType = s.TargetType.ToString(),
            ChargeTime = s.ChargeTime,
            CastDuration = s.CastDuration,
            Range = s.Range,
            HalfCostPerk = names.Ref(s.HalfCostPerk),
            EquipmentType = names.Ref(s.EquipmentType),
            MenuDisplayObject = names.Key(s.MenuDisplayObject),
            Keywords = Keywords(s.Keywords, names),
            Flags = FlagList(s.Flags),
            Effects = Effects(s.Effects, names, winningMgef),
        };
        bool manual = s.Flags.HasFlag(SpellDataFlag.ManualCostCalc);
        int? auto = CostCalculator.SpellAutoCost(s.Effects, winningMgef);
        dto.Cost = new CostDto
        {
            BaseCost = s.BaseCost,
            ManualCostCalc = manual,
            ComputedAutoCost = auto,
            CostDrift = manual || auto is null ? null : auto - (int)s.BaseCost,
            CostMatchesStored = manual || auto is null ? null : auto == (int)s.BaseCost,
        };
        dto.School = School(s.Effects, winningMgef, schoolNames);
        return dto;
    }

    /// <summary>School = MagicSkill of the costliest effect (the CK's rule).</summary>
    private static SchoolDto? School(IReadOnlyList<IEffectGetter>? effects,
        IReadOnlyDictionary<FormKey, IMagicEffectGetter> winningMgef,
        IReadOnlyDictionary<ActorValue, string> schoolNames)
    {
        if (effects is null) return null;
        IMagicEffectGetter? best = null;
        double bestCost = -1;
        foreach (var e in effects)
        {
            if (!winningMgef.TryGetValue(e.BaseEffect.FormKey, out var mgef)) continue;
            double c = CostCalculator.EffectCost(mgef, e.Data?.Magnitude ?? 0, e.Data?.Duration ?? 0);
            if (c > bestCost) { bestCost = c; best = mgef; }
        }
        if (best is null || best.MagicSkill == ActorValue.None) return null;
        return new SchoolDto
        {
            ActorValue = best.MagicSkill.ToString(),
            DisplayName = schoolNames.TryGetValue(best.MagicSkill, out var n) ? n : best.MagicSkill.ToString(),
            Source = "costliestEffect",
        };
    }

    public static MagicEffectDto MagicEffect(IMagicEffectGetter m, NameIndex names)
    {
        return new MagicEffectDto
        {
            FormKey = m.FormKey.ToString(),
            EditorId = m.EditorID,
            Name = Str(m.Name),
            Description = Str(m.Description),
            BaseCost = m.BaseCost,
            MagicSkill = m.MagicSkill == ActorValue.None ? null : m.MagicSkill.ToString(),
            ResistValue = m.ResistValue == ActorValue.None ? null : m.ResistValue.ToString(),
            SecondActorValue = m.SecondActorValue == ActorValue.None ? null : m.SecondActorValue.ToString(),
            SecondActorValueWeight = m.SecondActorValueWeight,
            Archetype = m.Archetype.Type.ToString(),
            ArchetypeActorValue = m.Archetype.ActorValue == ActorValue.None ? null : m.Archetype.ActorValue.ToString(),
            ArchetypeAssociation = ArchetypeAssociation(m.Archetype),
            CastType = m.CastType.ToString(),
            TargetType = m.TargetType.ToString(),
            TaperWeight = m.TaperWeight,
            TaperCurve = m.TaperCurve,
            TaperDuration = m.TaperDuration,
            MinimumSkillLevel = m.MinimumSkillLevel,
            SpellmakingArea = m.SpellmakingArea,
            SpellmakingCastingTime = m.SpellmakingCastingTime,
            SkillUsageMultiplier = m.SkillUsageMultiplier,
            DualCastScale = m.DualCastScale,
            DualCastArt = names.Key(m.DualCastArt),
            Projectile = names.Key(m.Projectile),
            Explosion = names.Key(m.Explosion),
            PerkToApply = names.Ref(m.PerkToApply),
            EquipAbility = names.Ref(m.EquipAbility),
            CastingLight = names.Key(m.CastingLight),
            ImageSpaceModifier = names.Key(m.ImageSpaceModifier),
            CastingSoundLevel = m.CastingSoundLevel.ToString(),
            CounterEffects = m.CounterEffects.Count == 0 ? null
                : m.CounterEffects.Select(c => c.FormKey.ToString()).ToList(),
            Keywords = Keywords(m.Keywords, names),
            Flags = FlagList(m.Flags),
            Conditions = Conditions(m.Conditions),
            Scripts = Scripts(m.VirtualMachineAdapter),
        };
    }

    private static string? ArchetypeAssociation(IAMagicEffectArchetypeGetter arch)
    {
        // Typed archetype subclasses carry an Association form link (spell, race, keyword, …).
        var prop = arch.GetType().GetProperty("Association");
        if (prop?.GetValue(arch) is IFormLinkIdentifier fli && !fli.FormKey.IsNull)
            return fli.FormKey.ToString();
        return null;
    }

    private static List<ScriptDto>? Scripts(IVirtualMachineAdapterGetter? vmad)
    {
        if (vmad is null || vmad.Scripts.Count == 0) return null;
        var list = new List<ScriptDto>(vmad.Scripts.Count);
        foreach (var s in vmad.Scripts)
        {
            var dto = new ScriptDto { Name = s.Name };
            if (s.Properties.Count > 0)
            {
                dto.Properties = new List<ScriptPropertyDto>(s.Properties.Count);
                foreach (var p in s.Properties)
                {
                    dto.Properties.Add(new ScriptPropertyDto
                    {
                        Name = p.Name,
                        Type = p.GetType().Name.Replace("ScriptProperty", "").Replace("Script", ""),
                        Value = ScriptPropertyValue(p),
                    });
                }
            }
            list.Add(dto);
        }
        return list;
    }

    private static string? ScriptPropertyValue(IScriptPropertyGetter p) => p switch
    {
        IScriptObjectPropertyGetter o => o.Object.FormKey.IsNull ? null : o.Object.FormKey.ToString(),
        IScriptFloatPropertyGetter f => f.Data.ToString(System.Globalization.CultureInfo.InvariantCulture),
        IScriptIntPropertyGetter i => i.Data.ToString(),
        IScriptBoolPropertyGetter b => b.Data.ToString(),
        IScriptStringPropertyGetter s => s.Data,
        _ => null,
    };

    public static EnchantmentDto Enchantment(IObjectEffectGetter e, NameIndex names,
        IReadOnlyDictionary<FormKey, IMagicEffectGetter> winningMgef)
    {
        return new EnchantmentDto
        {
            FormKey = e.FormKey.ToString(),
            EditorId = e.EditorID,
            Name = Str(e.Name),
            EnchantmentCost = e.EnchantmentCost,
            EnchantmentAmount = (uint)e.EnchantmentAmount,
            EnchantType = e.EnchantType.ToString(),
            CastType = e.CastType.ToString(),
            TargetType = e.TargetType.ToString(),
            ChargeTime = e.ChargeTime,
            BaseEnchantment = names.Key(e.BaseEnchantment),
            WornRestrictions = names.Key(e.WornRestrictions),
            Flags = FlagList(e.Flags),
            Effects = Effects(e.Effects, names, winningMgef),
        };
    }

    public static ScrollDto Scroll(IScrollGetter s, NameIndex names,
        IReadOnlyDictionary<FormKey, IMagicEffectGetter> winningMgef)
    {
        bool manual = s.Flags.HasFlag(SpellDataFlag.ManualCostCalc);
        int? auto = CostCalculator.SpellAutoCost(s.Effects, winningMgef);
        return new ScrollDto
        {
            FormKey = s.FormKey.ToString(),
            EditorId = s.EditorID,
            Name = Str(s.Name),
            Description = Str(s.Description),
            Type = s.Type.ToString(),
            CastType = s.CastType.ToString(),
            TargetType = s.TargetType.ToString(),
            Cost = new CostDto
            {
                BaseCost = s.BaseCost,
                ManualCostCalc = manual,
                ComputedAutoCost = auto,
                CostDrift = manual || auto is null ? null : auto - (int)s.BaseCost,
                CostMatchesStored = manual || auto is null ? null : auto == (int)s.BaseCost,
            },
            ChargeTime = s.ChargeTime,
            CastDuration = s.CastDuration,
            Range = s.Range,
            HalfCostPerk = names.Ref(s.HalfCostPerk),
            Value = s.Value,
            Weight = s.Weight,
            Keywords = Keywords(s.Keywords, names),
            Flags = FlagList(s.Flags),
            Effects = Effects(s.Effects, names, winningMgef),
        };
    }

    public static IngestibleDto Ingestible(IIngestibleGetter a, NameIndex names,
        IReadOnlyDictionary<FormKey, IMagicEffectGetter> winningMgef)
    {
        return new IngestibleDto
        {
            FormKey = a.FormKey.ToString(),
            EditorId = a.EditorID,
            Name = Str(a.Name),
            Description = Str(a.Description),
            Value = a.Value,
            Weight = a.Weight,
            Flags = FlagList(a.Flags),
            Addiction = names.Ref(a.Addiction),
            AddictionChance = a.AddictionChance,
            Keywords = Keywords(a.Keywords, names),
            Effects = Effects(a.Effects, names, winningMgef),
        };
    }

    public static ShoutDto Shout(IShoutGetter s, NameIndex names)
    {
        return new ShoutDto
        {
            FormKey = s.FormKey.ToString(),
            EditorId = s.EditorID,
            Name = Str(s.Name),
            Description = Str(s.Description),
            WordsOfPower = s.WordsOfPower.Count == 0 ? null : s.WordsOfPower.Select(w => new ShoutWordDto
            {
                Word = names.Ref(w.Word),
                Spell = names.Ref(w.Spell),
                RecoveryTime = w.RecoveryTime,
            }).ToList(),
        };
    }

    public static LeveledSpellDto LeveledSpell(ILeveledSpellGetter l, NameIndex names)
    {
        return new LeveledSpellDto
        {
            FormKey = l.FormKey.ToString(),
            EditorId = l.EditorID,
            ChanceNone = (byte)Math.Round(l.ChanceNone * 100),
            Flags = FlagList(l.Flags),
            Entries = l.Entries is null || l.Entries.Count == 0 ? null
                : l.Entries.Select(e => new LeveledSpellEntryDto
                {
                    Level = (short)(e.Data?.Level ?? 0),
                    Spell = e.Data is null ? null : names.Ref(e.Data.Reference),
                    Count = (short)(e.Data?.Count ?? 0),
                }).ToList(),
        };
    }

    public static GameSettingDto GameSetting(IGameSettingGetter g)
    {
        object? value = g switch
        {
            IGameSettingFloatGetter f => f.Data,
            IGameSettingIntGetter i => i.Data,
            IGameSettingBoolGetter b => b.Data,
            IGameSettingStringGetter s => s.Data?.String,
            _ => null,
        };
        return new GameSettingDto
        {
            FormKey = g.FormKey.ToString(),
            EditorId = g.EditorID,
            Value = value,
        };
    }
}
