// Zenderal - Chocolate Poise Faction Fix (NetScriptFramework plugin)
//
// Chocolate Poise - Reforged (ChocolatePoiseReforged.dll v4.0.0) looks up vanilla Skyrim's
// ForceFullBodyStagger faction by hardcoded FormID 0x10CED7. In Enderal that ID is a placed
// reference (cell QKerker), so the lookup's faction-type check discards it, the field stays
// null, and every poise break then runs a_target->AddToFaction(nullptr, 0) with no null check
// (src/PoiseAV.cpp). The null faction entry crashes the next faction-reaction lookup on that
// actor at SkyrimSE.exe+19E6A0 (TESReactionForm).
//
// Fix: once data is loaded (main menu), point that field at the ForceFullBodyStagger faction
// the Chocolate Poise Enderal patch already ships (ChocolatePoise - Enderal.esp, 0x800). The
// same patch's PlayerStaggerRoot idle conditions on that faction, so full-body stagger also
// works. The write only happens if the DLL's code bytes match the build this was written for.
using System;
using System.IO;
using System.Linq;
using NetScriptFramework;
using NetScriptFramework.SkyrimSE;

namespace ZenCPRFactionFix
{
    public sealed class Plugin : NetScriptFramework.Plugin
    {
        public override string Key => "zen_cpr_faction_fix";
        public override string Name => "Zenderal - Chocolate Poise Faction Fix";
        public override string Author => "Zenderal";
        public override int Version => 1;
        public override int RequiredFrameworkVersion => 9;
        public override int RequiredLibraryVersion => 13;

        const string ModuleName = "ChocolatePoiseReforged.dll";
        // RetrieveFullBodyStaggerFaction: "mov ecx, 0x10CED7" at this RVA
        const long LookupSiteRva = 0x5B542;
        static readonly byte[] LookupSiteBytes = { 0xB9, 0xD7, 0xCE, 0x10, 0x00 };
        // PoiseAV singleton (function-local static) at 0x139100; ForceFullBodyStagger field at +8
        const long FactionFieldRva = 0x139108;
        const string FactionFile = "ChocolatePoise - Enderal.esp";
        const uint FactionId = 0x800;

        static readonly string LogPath = Path.Combine("Data", "NetScriptFramework", "ZenCPRFactionFix.log");

        static void Log(string msg)
        {
            try { File.AppendAllText(LogPath, DateTime.Now.ToString("HH:mm:ss.fff") + " " + msg + Environment.NewLine); }
            catch { }
        }

        protected override bool Initialize(bool loadedAny)
        {
            Log("=== ZenCPRFactionFix started");
            // Every main-menu entry: cheap, and covers a game that reloads data.
            Events.OnMainMenu.Register(e => TryFix(), 0, 0);
            return true;
        }

        static void TryFix()
        {
            try
            {
                var mod = System.Diagnostics.Process.GetCurrentProcess().Modules
                    .Cast<System.Diagnostics.ProcessModule>()
                    .FirstOrDefault(m => string.Equals(m.ModuleName, ModuleName, StringComparison.OrdinalIgnoreCase));
                if (mod == null) { Log(ModuleName + " not loaded - nothing to do."); return; }
                var b = mod.BaseAddress;

                var site = Memory.ReadBytes(new IntPtr(b.ToInt64() + LookupSiteRva), LookupSiteBytes.Length);
                if (!site.SequenceEqual(LookupSiteBytes))
                {
                    Log("Code bytes at lookup site differ (" + BitConverter.ToString(site) + ") - unknown CPR build, NOT patching.");
                    return;
                }

                var field = new IntPtr(b.ToInt64() + FactionFieldRva);
                var current = Memory.ReadPointer(field);
                if (current != IntPtr.Zero) { Log("Faction field already set (" + current.ToString("X") + ") - leaving it."); return; }

                var faction = TESForm.LookupFormFromFile(FactionId, FactionFile);
                if (faction == null) { Log("Faction 0x800 not found in " + FactionFile + " - is it enabled? NOT patching."); return; }

                Memory.WritePointer(field, faction.Address);
                Log("Patched: ForceFullBodyStagger -> " + FactionFile + " (form " + faction.FormId.ToString("X8") + ")");
            }
            catch (Exception ex)
            {
                Log("FAILED: " + ex);
            }
        }
    }
}
