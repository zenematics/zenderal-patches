# List-shaped records and vendor stock

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

## A LIST-SHAPED record is replaced wholesale, so a late override silently deletes stock

**[verified 2026-08-11]** This is the single most productive bug class found in this list so far —
**214 entries across seven merchant chests**, every one installed, enabled and unobtainable, all
now restored by `Zenderal - Kata Fixes.esp`. Read this before authoring any patch that touches a
vendor chest, an NPC inventory or a leveled list.

The engine does not merge a Container's `Items:`, an NPC's inventory or a LeveledItem's `Entries:`.
**The last plugin to override the record supplies the entire list.** So when mod A adds 45 spell
tomes to a merchant, and unrelated mod B overrides that same merchant later for its own reasons,
A's 45 tomes are gone. This is guardrail 5 seen from the receiving end, and it is invisible: both
mods are installed, both enabled, the merchant exists and has plenty of stock, and the items are
simply not in the game. No log line, no missing master, nothing to notice.

**`EGO SE - Leveling Redone.esp` is the list's second dominant conflict source, after EGO itself.**
It sits at load order **138** — far later than the content mods — and overrides **50 containers**,
carrying none of any earlier mod's additions. It cost this list 160 Apocalypse spell tomes across
seven merchant chests, plus Kata's staves and xxOpenSpells' books.
`Zenderal - Kata Fixes.esp` now repairs all seven. Treat any record it touches as contested.

> **The load order MOVED under this analysis once already — re-read `loadorder.txt`, don't trust
> numbers written here.** **[verified 2026-08-20]** The 2026-08-11 audit saw Apocalypse at 125 and
> Leveling Redone at 166; the live Alpha 0.3 profile now has Leveling Redone at **138** and
> Apocalypse at **291** — the order *flipped*, so on any chest a Zenderal patch does not override,
> **Apocalypse's base-derived container records now win**, reverting EGO's and Leveling Redone's
> chest work. That is exactly how the "Ora Stonehand sells deprecated *Fire Ball*/*Chain Lightning*
> tomes" bug report happened: the rebuilt Apocalypse's Funkentanz/Torius/Steinschlag chest overrides
> were copied from **base Enderal's** records, which directly stock `_05E_SpellBookFireBall 08564A`
> and `_05E_SpellBookChainLightning 04DC94` — tomes teaching spells EGO renamed `*unused` with the
> "no longer used in the Gameplay Overhaul" description (EGO deliberately dropped both from its own
> chest overrides and never overrides those two Book records, so they keep the base "Fire Ball"
> spaced name). The seven-chest Kata Fixes merge already covers all three chests — but the bug
> shipped anyway because the **deployed `Zenderal - Kata Fixes.esp` was a stale 2026-08-09
> three-chest build** (no Steinschlag override): Gabrielle (Funkentanz, covered since the first
> build) looked fine while Ora (Steinschlag, added 2026-08-11) stayed broken. The auditor audits the
> *serialized source*, not the deployed binary, so it reports clean over a stale deploy — after any
> chest-merge change, verify the deployed `.esp` actually contains the new override (guardrail 7:
> `grep -c CCSteinschlag <esp>` is enough).

**Run the auditor rather than remembering this:**

```
python src/KataFixes/tools/00-audit-vendor-conflicts.py        # read-only; --all shows patched ones too
```

It reads the live load order from the MO2 profile, walks every serialized plugin under
`reference/mods/`, and reports each list-shaped record where a later plugin drops an earlier one's
entries — filtering out deliberate drops (see below) and what a Zenderal patch already covers.
**It currently reports the list clean: no collateral stock loss across 1837 records.** It only sees
what is serialized, so a silent report means "none among the trees present", **not** "none":
decompile the mod first if you are patching near it.

> **COLLATERAL vs DELIBERATE — check this before calling anything a bug.** A dropped entry is only
> a defect if **the winner does not declare the loser as a master.** A plugin cannot make a decision
> about records it cannot see. Leveling Redone masters only `Skyrim.esm`, FS and EGO, so it had no
> idea Apocalypse's tomes or Kata's staves were ever in those seven chests — pure collateral. But it
> *does* master EGO, so its Gaboff chest dropping EGO's two Gaboff-priced learning books and
> substituting the standard cheaper ones (`00775E` at 265g for `00840A` at 400g, base Enderal's
> `0CE135` for `00840B`) is the mod doing its job — as is stripping ~25 `_00E_Lehrbuch*` /
> `_00E_Handwerksbuch*` skill books off Adlerauge and the Blacksmith. It is a **leveling** overhaul
> and those are leveling items. Likewise `EGO - KataPUMB Spell Package.esp` swapping
> `_60E_XionFireNovaMythic` for its own `_60E_XionRecitalMythic`.
>
> **[verified 2026-08-11]** All five of those read as "lost stock" on a naive entry diff and all five
> are correct behaviour; the auditor's first version reported them and nearly bought a patch that
> would have fought a rebalance mod. And note the second trap inside the collateral class: a
> **substitution is not a deletion** — compare entry counts and read both records before patching.

Two more things to get right when fixing a genuine one, both easy to get backwards:

1. **Start from the WINNER's record, not the master's.** The winner's trims and value changes are
   deliberate balance work and must be forwarded.
2. **Re-append only entries whose FormKey suffix is the LOSER'S OWN plugin.** An entry carrying a
   *master's* suffix that the winner lacks is the winner deliberately deleting the master's stock —
   restoring those reverts its rebalance. Leveling Redone trims hard: it cuts Milbert from 91
   entries to 33. `src/KataFixes/tools/01-merge-vendor-chests.py` is the worked example, and it
   asserts every count so a mod update fails the build instead of shipping quietly.

**One owner per record.** Whichever Zenderal plugin overrides a contested record owns it alone; a
second one of ours touching it re-creates the exact bug (`Kata Fixes` is 303, `Magic Patches` 304,
so Magic Patches would win and wipe Kata's staves). See the ownership split in `CLAUDE.md`'s allocations table and [`../patches/`](../patches/).
