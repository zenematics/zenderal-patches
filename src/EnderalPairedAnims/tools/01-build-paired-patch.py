"""Build the Pandora-native patch that puts Enderal's six FNIS paired/killmove scenes back into
the third-person 0_master graph.

Pandora 5.0.0-beta cannot build FNIS `pa`/`km` lines (see arch-docs/patches/EnderalPairedAnims.md),
so this script lifts exactly what FNIS put into Enderal's own 0_master.hkx and re-expresses it as
edits on Pandora's vanilla template:

  * every node reachable from the FNIS states FNIS added to KillMove_Behavior and
    MT_PairedAnimationsBehavior -> new nodes, renamed #zpaired$N
  * those states appended to the two state machines' `states`
  * FNIS's wildcard transitions appended to the two machines' transition arrays
  * the 12 FNIS events appended to eventNames/eventInfos; every reference to them written as
    $eventID[name]$ so Pandora re-resolves the index after other mods add events

Inputs are XML conversions made with tools/hkxconv (see the doc):
  enderal.xml  - <Stock Game>/Data/meshes/actors/character/behaviors/0_master.hkx   (plain)
  pandora.xml  - <Pandora>/Pandora_Engine/Skyrim/Template/actors/character/behaviors/0_master.hkx (--meta)

usage: python 01-build-paired-patch.py enderal.xml pandora.xml <out patches/0_master.xml>
"""
import re
import sys
import xml.etree.ElementTree as ET

MOD = "zpaired"
REF = re.compile(r"#\d+")
EVENT_PARAMS = {"id", "eventId", "enterEventId", "exitEventId"}
# The scenes this patch exists for: (player event, NPC event). Asserted below.
EXPECTED_EVENTS = {"CaliaMassacre", "HugB", "Kiss2Female", "Kiss2Male", "KissMaleFemale", "KissFemaleMale"}


def load(path):
    objs = {}
    for o in ET.parse(path).getroot().iter("hkobject"):
        if o.get("name"):
            objs[o.get("name")] = o
    return objs


def pname(o):
    p = o.find("hkparam[@name='name']")
    return p.text if p is not None else None


def param(o, name):
    p = o.find(f"hkparam[@name='{name}']")
    if p is None:
        raise SystemExit(f"{o.get('name')} has no hkparam {name}")
    return p


def ref_lists(o):
    out = []
    for hp in o.iter("hkparam"):
        txt = (hp.text or "").strip()
        if hp.find("hkobject") is None and txt and re.fullmatch(r"(#\d+\s*)+", txt):
            out.append((hp.get("name"), txt.split()))
    return out


def find_one(objs, cls, name=None):
    hits = [n for n, o in objs.items() if o.get("class") == cls and (name is None or pname(o) == name)]
    if len(hits) != 1:
        raise SystemExit(f"expected one {cls} {name}, found {hits}")
    return hits[0]


def string_data(objs):
    o = objs[find_one(objs, "hkbBehaviorGraphStringData")]
    return [x.text for x in param(o, "eventNames")], [x.text for x in param(o, "variableNames")]


E = load(sys.argv[1])
P = load(sys.argv[2])
out_path = sys.argv[3]

# --- align Enderal's graph onto Pandora's template (same vanilla tree; FNIS only adds) ---------
emap = {}


def align(e, p):
    if e in emap:
        return
    emap[e] = p
    pd = {}
    for k, v in ref_lists(P[p]):
        pd.setdefault(k, []).append(v)
    ed = {}
    for k, v in ref_lists(E[e]):
        ed.setdefault(k, []).append(v)
    for k, elists in ed.items():
        for el, pl in zip(elists, pd.get(k, [])):
            if len(el) == len(pl):
                for a, b in zip(el, pl):
                    align(a, b)
            else:
                by_name = {pname(P[x]): x for x in pl}
                for a in el:
                    if pname(E[a]) in by_name:
                        align(a, by_name[pname(E[a])])


align(find_one(E, "hkRootLevelContainer"), find_one(P, "hkRootLevelContainer"))

e_events, e_vars = string_data(E)
p_events, p_vars = string_data(P)
assert e_events[: len(p_events)] == p_events, "Enderal's vanilla event list differs from Pandora's"
assert e_vars[: len(p_vars)] == p_vars, "Enderal's vanilla variable list differs from Pandora's"
VANILLA_EVENTS = len(p_events)
VANILLA_VARS = len(p_vars)

# --- the two state machines FNIS extended -------------------------------------------------------
TARGETS = {}  # enderal SM -> (pandora SM, enderal transitions array, pandora transitions array)
for sm_name in ("KillMove_Behavior", "MT_PairedAnimationsBehavior"):
    e_sm = find_one(E, "hkbStateMachine", sm_name)
    p_sm = emap[e_sm]
    assert pname(P[p_sm]) == sm_name
    e_tr = param(E[e_sm], "wildcardTransitions").text.strip()
    p_tr = param(P[p_sm], "wildcardTransitions").text.strip()
    assert emap[e_tr] == p_tr
    TARGETS[e_sm] = (p_sm, e_tr, p_tr)

new_states = {}  # enderal SM -> [enderal state nodes not in the template]
for e_sm in TARGETS:
    states = param(E[e_sm], "states").text.split()
    new_states[e_sm] = [s for s in states if s not in emap]
    assert all(s in emap for s in states if s not in new_states[e_sm])

# --- closure of new nodes -----------------------------------------------------------------------
order = list(E)  # document order -> stable numbering
closure = set()
stack = [s for v in new_states.values() for s in v]
while stack:
    n = stack.pop()
    if n in closure or n in emap:
        continue
    closure.add(n)
    for r in REF.findall(ET.tostring(E[n], encoding="unicode")):
        if r != n and r in E:
            stack.append(r)
new_nodes = [n for n in order if n in closure]
rename = {n: f"#{MOD}${i}" for i, n in enumerate(new_nodes)}


def remap_ref(r):
    if r in rename:
        return rename[r]
    if r in emap:
        return emap[r]
    raise SystemExit(f"reference {r} is neither new nor aligned")


used_events = set()


def rewrite(el):
    """Rename refs, turn FNIS event indices into $eventID[]$; assert no FNIS variable is used."""
    for hp in el.iter("hkparam"):
        txt = (hp.text or "").strip()
        if hp.find("hkobject") is None and txt and re.fullmatch(r"(#\d+\s*)+", txt):
            hp.text = " ".join(remap_ref(r) for r in txt.split())
        elif hp.get("name") in EVENT_PARAMS and re.fullmatch(r"-?\d+", txt):
            i = int(txt)
            if i >= VANILLA_EVENTS:
                used_events.add(e_events[i])
                hp.text = f"$eventID[{e_events[i]}]$"
        elif hp.get("name") == "variableIndex" and int(txt) >= VANILLA_VARS:
            raise SystemExit(f"FNIS variable {e_vars[int(txt)]} used - not handled")
    if el.tag == "hkobject" and el.get("name") in rename:
        el.set("name", rename[el.get("name")])
    return el


def copy(el):
    return ET.fromstring(ET.tostring(el, encoding="unicode"))


new_objs = [rewrite(copy(E[n])) for n in new_nodes]

# --- appended transitions: Enderal's array = template's array + FNIS's tail ---------------------
appended_transitions = {}
for e_sm, (p_sm, e_tr, p_tr) in TARGETS.items():
    e_list = list(param(E[e_tr], "transitions"))
    p_list = list(param(P[p_tr], "transitions"))
    head = [rewrite(copy(t)) for t in e_list[: len(p_list)]]
    for a, b in zip(head, p_list):
        assert re.sub(r"\s+", "", ET.tostring(a, encoding="unicode")) == re.sub(
            r"\s+", "", ET.tostring(b, encoding="unicode")
        ), f"{e_tr}: a vanilla transition differs"
    tail = [rewrite(copy(t)) for t in e_list[len(p_list):]]
    new_ids = {int(param(E[s], "stateId").text) for s in new_states[e_sm]}
    assert {int(param(t, "toStateId").text) for t in tail} == new_ids, "transitions != new states"
    appended_transitions[p_tr] = tail

fnis_events = e_events[VANILLA_EVENTS:]
assert used_events == set(fnis_events), (used_events, fnis_events)
assert set(fnis_events) == EXPECTED_EVENTS | {"pa_" + e for e in EXPECTED_EVENTS}, fnis_events
e_infos = list(param(E[find_one(E, "hkbBehaviorGraphData")], "eventInfos"))[VANILLA_EVENTS:]

# --- write ----------------------------------------------------------------------------------------
root = ET.Element("patch")
ET.SubElement(root, "Append", path="").extend(new_objs)
for e_sm, (p_sm, _, _) in TARGETS.items():
    ET.SubElement(root, "Append", path=f"{p_sm}/states").text = " ".join(
        rename[s] for s in new_states[e_sm]
    )
for p_tr, tail in appended_transitions.items():
    ET.SubElement(root, "Append", path=f"{p_tr}/transitions").extend(tail)
sd = find_one(P, "hkbBehaviorGraphStringData")
gd = find_one(P, "hkbBehaviorGraphData")
ev = ET.SubElement(root, "Append", path=f"{sd}/eventNames")
for name in fnis_events:
    ET.SubElement(ev, "hkcstring").text = name
ET.SubElement(root, "Append", path=f"{gd}/eventInfos").extend(copy(i) for i in e_infos)

ET.indent(root, space="\t")
with open(out_path, "w", encoding="utf-8", newline="\r\n") as f:
    f.write(ET.tostring(root, encoding="unicode"))
    f.write("\n")

print(f"new nodes: {len(new_nodes)}")
for e_sm, states in new_states.items():
    print(f"  {pname(E[e_sm])} ({TARGETS[e_sm][0]}): +{len(states)} states "
          f"{[pname(E[s]) for s in states]}, +{len(appended_transitions[TARGETS[e_sm][2]])} transitions")
print(f"events: +{len(fnis_events)} {fnis_events}")
skipped = [n for n in E if n not in emap and n not in closure]
print(f"FNIS nodes NOT carried (other FNIS behaviours Pandora already splices): {len(skipped)}")
for n in skipped:
    print(f"  {n} {E[n].get('class')} {pname(E[n])}")
