namespace MagicExtract.Projections;

// Field names follow Mutagen's Loqui definitions (camelCased by the serializer) so the JSON,
// the Spriggit YAML and xEdit share one vocabulary. Records are addressed by formKey — the
// stable identity a future write-back generator diffs against.

/// <summary>Every top-level record DTO: addressed by FormKey, carries provenance.</summary>
public interface IRecordDto
{
    string FormKey { get; }
    ProvenanceDto? Provenance { get; set; }
}

/// <summary>A FormKey reference decorated with the winning record's EditorID/Name when known.</summary>
public sealed class RefDto
{
    public required string FormKey { get; init; }
    public string? EditorId { get; set; }
    public string? Name { get; set; }
}

public sealed class ProvenanceDto
{
    public required string DefinedIn { get; set; }
    public bool IsNewRecord { get; set; }
    public bool IsInjected { get; set; }
    public required string Winner { get; set; }
    public int WinnerLoadOrderIndex { get; set; }
    public required List<string> Chain { get; set; }
    public List<string>? ChangedFields { get; set; }
    public float? WinnerHeaderVersion { get; set; }
    public bool WinnerNeedsBees { get; set; }
}

public sealed class ConditionDto
{
    public required string Function { get; set; }
    public string? RunOn { get; set; }
    public string? Reference { get; set; }
    public Dictionary<string, string>? Parameters { get; set; }
    public required string Operator { get; set; }
    public object? Value { get; set; }   // float, or a Ref string for ConditionGlobal
    public bool Or { get; set; }
}

public sealed class EffectDto
{
    public int Index { get; set; }
    public RefDto? BaseEffect { get; set; }
    public float Magnitude { get; set; }
    public int Area { get; set; }
    public int Duration { get; set; }
    /// <summary>floor(mgefBaseCost * max(mag,1)^1.1 * ((dur==0?10:dur)/10)^1.1) using the WINNING MGEF.</summary>
    public int? EffectCost { get; set; }
    public string? Archetype { get; set; }
    public string? ActorValue { get; set; }
    public List<ConditionDto>? Conditions { get; set; }
}

public sealed class SchoolDto
{
    public required string ActorValue { get; set; }
    public required string DisplayName { get; set; }
    public required string Source { get; set; }
}

public sealed class CostDto
{
    public uint BaseCost { get; set; }
    public bool ManualCostCalc { get; set; }
    public int? ComputedAutoCost { get; set; }
    public int? CostDrift { get; set; }
    public bool? CostMatchesStored { get; set; }
}

public sealed class SpellDto : IRecordDto
{
    public required string FormKey { get; init; }
    public string? EditorId { get; set; }
    public string? Name { get; set; }
    public string? Description { get; set; }
    public string? Type { get; set; }
    public string? CastType { get; set; }
    public string? TargetType { get; set; }
    public SchoolDto? School { get; set; }
    public CostDto? Cost { get; set; }
    public float ChargeTime { get; set; }
    public float CastDuration { get; set; }
    public float Range { get; set; }
    public RefDto? HalfCostPerk { get; set; }
    public RefDto? EquipmentType { get; set; }
    public string? MenuDisplayObject { get; set; }
    public List<RefDto>? Keywords { get; set; }
    public List<string>? Flags { get; set; }
    public List<EffectDto>? Effects { get; set; }
    /// <summary>Winning Book records whose Teaches points at this spell — the player-obtainable set.
    /// Null means no book teaches it (NPC-only, trap, voice, script-granted, …).</summary>
    public List<RefDto>? TaughtBy { get; set; }
    public ProvenanceDto? Provenance { get; set; }
}

public sealed class ScriptPropertyDto
{
    public required string Name { get; set; }
    public string? Type { get; set; }
    public string? Value { get; set; }
}

public sealed class ScriptDto
{
    public required string Name { get; set; }
    public List<ScriptPropertyDto>? Properties { get; set; }
}

public sealed class UsedByDto
{
    public List<string>? Spells { get; set; }
    public List<string>? Scrolls { get; set; }
    public List<string>? Enchantments { get; set; }
    public List<string>? Ingestibles { get; set; }
}

public sealed class MagicEffectDto : IRecordDto
{
    public required string FormKey { get; init; }
    public string? EditorId { get; set; }
    public string? Name { get; set; }
    public string? Description { get; set; }
    public float BaseCost { get; set; }
    public string? MagicSkill { get; set; }
    public string? ResistValue { get; set; }
    public string? SecondActorValue { get; set; }
    public float SecondActorValueWeight { get; set; }
    public string? Archetype { get; set; }
    public string? ArchetypeActorValue { get; set; }
    public string? ArchetypeAssociation { get; set; }
    public string? CastType { get; set; }
    public string? TargetType { get; set; }
    public float TaperWeight { get; set; }
    public float TaperCurve { get; set; }
    public float TaperDuration { get; set; }
    public uint MinimumSkillLevel { get; set; }
    public uint SpellmakingArea { get; set; }
    public float SpellmakingCastingTime { get; set; }
    public float SkillUsageMultiplier { get; set; }
    public float DualCastScale { get; set; }
    public string? DualCastArt { get; set; }
    public string? Projectile { get; set; }
    public string? Explosion { get; set; }
    public RefDto? PerkToApply { get; set; }
    public RefDto? EquipAbility { get; set; }
    public string? CastingLight { get; set; }
    public string? ImageSpaceModifier { get; set; }
    public string? CastingSoundLevel { get; set; }
    public List<string>? CounterEffects { get; set; }
    public List<RefDto>? Keywords { get; set; }
    public List<string>? Flags { get; set; }
    public List<ConditionDto>? Conditions { get; set; }
    public List<ScriptDto>? Scripts { get; set; }
    public UsedByDto? UsedBy { get; set; }
    public ProvenanceDto? Provenance { get; set; }
}

public sealed class EnchantmentDto : IRecordDto
{
    public required string FormKey { get; init; }
    public string? EditorId { get; set; }
    public string? Name { get; set; }
    public uint EnchantmentCost { get; set; }
    public uint EnchantmentAmount { get; set; }
    public string? EnchantType { get; set; }
    public string? CastType { get; set; }
    public string? TargetType { get; set; }
    public float ChargeTime { get; set; }
    public string? BaseEnchantment { get; set; }
    public string? WornRestrictions { get; set; }
    public List<string>? Flags { get; set; }
    public List<EffectDto>? Effects { get; set; }
    public ProvenanceDto? Provenance { get; set; }
}

public sealed class ScrollDto : IRecordDto
{
    public required string FormKey { get; init; }
    public string? EditorId { get; set; }
    public string? Name { get; set; }
    public string? Description { get; set; }
    public string? Type { get; set; }
    public string? CastType { get; set; }
    public string? TargetType { get; set; }
    public CostDto? Cost { get; set; }
    public float ChargeTime { get; set; }
    public float CastDuration { get; set; }
    public float Range { get; set; }
    public RefDto? HalfCostPerk { get; set; }
    public uint Value { get; set; }
    public float Weight { get; set; }
    public List<RefDto>? Keywords { get; set; }
    public List<string>? Flags { get; set; }
    public List<EffectDto>? Effects { get; set; }
    public ProvenanceDto? Provenance { get; set; }
}

public sealed class IngestibleDto : IRecordDto
{
    public required string FormKey { get; init; }
    public string? EditorId { get; set; }
    public string? Name { get; set; }
    public string? Description { get; set; }
    public uint Value { get; set; }
    public float Weight { get; set; }
    public List<string>? Flags { get; set; }
    public RefDto? Addiction { get; set; }
    public float AddictionChance { get; set; }
    public List<RefDto>? Keywords { get; set; }
    public List<EffectDto>? Effects { get; set; }
    public ProvenanceDto? Provenance { get; set; }
}

public sealed class ShoutWordDto
{
    public RefDto? Word { get; set; }
    public RefDto? Spell { get; set; }
    public float RecoveryTime { get; set; }
}

public sealed class ShoutDto : IRecordDto
{
    public required string FormKey { get; init; }
    public string? EditorId { get; set; }
    public string? Name { get; set; }
    public string? Description { get; set; }
    public List<ShoutWordDto>? WordsOfPower { get; set; }
    public ProvenanceDto? Provenance { get; set; }
}

public sealed class LeveledSpellEntryDto
{
    public short Level { get; set; }
    public RefDto? Spell { get; set; }
    public short Count { get; set; }
}

public sealed class LeveledSpellDto : IRecordDto
{
    public required string FormKey { get; init; }
    public string? EditorId { get; set; }
    public byte ChanceNone { get; set; }
    public List<string>? Flags { get; set; }
    public List<LeveledSpellEntryDto>? Entries { get; set; }
    public ProvenanceDto? Provenance { get; set; }
}

public sealed class GameSettingDto : IRecordDto
{
    public required string FormKey { get; init; }
    public string? EditorId { get; set; }
    public object? Value { get; set; }
    public ProvenanceDto? Provenance { get; set; }
}
