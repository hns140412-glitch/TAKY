import json, hashlib
from pathlib import Path

ROOT = Path(r"D:\Git PWA\TAKY")
REG = ROOT / "MASTER" / "CHARACTER_VISUAL_ID_BACKFILL_REGISTRY_24_CANDIDATE_2026-10-08.json"

TRAITS = {
"07": {
  "character_class":"ANIMAL","species_or_body_type":"FOX_BIPED",
  "head_face":{
    "shape":"rounded fox head with short cream muzzle and broad cheek fur",
    "eyes":{"shape":"very large rounded","size":"large","spacing":"wide","angle":"soft","iris_color":"amber-gold","distinctive":"dark upper lash line with bright glossy highlights"},
    "brows":{"shape":"soft arched","weight":"light"},
    "nose_muzzle_beak":{"structure":"small dark fox nose over short cream muzzle","distinctive":"compact centered nose"},
    "mouth_lips":{"shape":"wide cheerful open smile","distinctive":"small visible canine teeth"},
    "ears_horns_antennae":{"structure":"very large upright fox ears with broad pale-pink inner ear"},
    "hair_fur_feather":{"silhouette":"short fluffy cream-blond layered crown and cheek fur","texture":"soft plush fur","hairline_or_pattern":"light cream crown blending into pale face"},
    "base_tone":"pale cream / warm blond",
    "unique_marks":["very large ears","fluffy pale tail","small white flower and gold-leaf cap ornament"],
    "resting_expression":"bright open smile"
  },
  "costume":{"identity_critical":["blue-white cap","cream hoodie","blue-white explorer jacket","dark cropped cargo pants","blue-white sneakers","dark backpack"],"signature_accessories":["white flower + gold leaf cap ornament","gold geometric hardware","dark paw gloves"],"signature_equipment":["backpack"],"materials":["soft fur","woven cap/hoodie/jacket","cargo textile","leather-like straps","metallic gold hardware","rubber sneaker sole"]},
  "palette":["pale cream fur","warm blond","royal blue","off-white","charcoal","gold"]
},
"08": {
  "character_class":"ANIMAL","species_or_body_type":"FOX_BIPED",
  "head_face":{
    "shape":"rounded fox head with white muzzle and cheek ruff",
    "eyes":{"shape":"large rounded","size":"large","spacing":"wide","angle":"soft","iris_color":"orange-amber","distinctive":"dark upper lashes; one-eye wink in source pose"},
    "brows":{"shape":"short dark arch","weight":"medium"},
    "nose_muzzle_beak":{"structure":"small black fox nose on short white muzzle","distinctive":"centered compact nose"},
    "mouth_lips":{"shape":"wide open cheerful smile","distinctive":"small visible canine teeth"},
    "ears_horns_antennae":{"structure":"large pointed fox ears with black/dark tips and pink inner ear"},
    "hair_fur_feather":{"silhouette":"bright orange spiky crown and cheek fur","texture":"soft dense fur","hairline_or_pattern":"orange crown with white muzzle/cheeks and dark ear tips"},
    "base_tone":"bright orange + white + dark ear tips",
    "unique_marks":["dark ear tips","large fluffy orange tail with pale tip","gold-rim goggles"],
    "resting_expression":"energetic playful smile"
  },
  "costume":{"identity_critical":["gold-rim goggles","white hoodie","red-white explorer jacket","dark cargo pants","red-white sneakers","dark backpack"],"signature_accessories":["goggles","gold buckles/hardware","dark paw gloves"],"signature_equipment":["explorer goggles","backpack"],"materials":["soft fur","woven hoodie/jacket","cargo textile","leather-like straps","metallic gold hardware","rubber sneaker sole"]},
  "palette":["orange","white","red","charcoal","navy-black","gold"]
},
"09": {
  "character_class":"ANIMAL","species_or_body_type":"DEER_BIPED",
  "head_face":{
    "shape":"small rounded deer face with cream muzzle and cheek fur",
    "eyes":{"shape":"large rounded-almond","size":"large","spacing":"wide","angle":"soft","iris_color":"amber-gold","distinctive":"dark upper lash line with glossy highlights"},
    "brows":{"shape":"soft arched","weight":"light"},
    "nose_muzzle_beak":{"structure":"small dark deer nose on short cream muzzle","distinctive":"compact rounded nose"},
    "mouth_lips":{"shape":"small closed gentle smile","distinctive":"subtle curved mouth"},
    "ears_horns_antennae":{"structure":"small pointed deer ears plus branching brown antlers"},
    "hair_fur_feather":{"silhouette":"layered light-brown crown and cheek tufts","texture":"soft plush fur","hairline_or_pattern":"warm tan crown with pale cream muzzle/cheeks"},
    "base_tone":"warm tan / light brown + cream",
    "unique_marks":["branching antlers","green leaf and pink-white flower crown","small fluffy tail"],
    "resting_expression":"gentle calm smile"
  },
  "costume":{"identity_critical":["cream-green hoodie/jacket with botanical motifs","dark cropped cargo pants","green-white sneakers","dark backpack"],"signature_accessories":["leaf/flower antler crown","gold hardware"],"signature_equipment":["backpack"],"materials":["soft fur","woven hoodie/jacket","cargo textile","leaf/flower decorative elements","leather-like straps","metallic gold hardware","rubber sneaker sole"]},
  "palette":["warm tan","cream","forest green","sage green","charcoal","pink-white flowers","gold"]
},
"10": {
  "character_class":"ANIMAL","species_or_body_type":"AVIAN_BIPED",
  "head_face":{
    "shape":"round avian head with broad white facial field",
    "eyes":{"shape":"very large rounded","size":"large","spacing":"wide","angle":"soft","iris_color":"violet-magenta","distinctive":"dark upper lash line and bright glossy highlights"},
    "brows":{"shape":"small lavender feather-brow marks","weight":"light"},
    "nose_muzzle_beak":{"structure":"short small yellow-orange beak","distinctive":"compact centered wedge beak"},
    "mouth_lips":{"shape":"open cheerful beak-mouth","distinctive":"pink mouth interior visible"},
    "ears_horns_antennae":{"structure":"no external ears; silhouette defined by feather crest and wings"},
    "hair_fur_feather":{"silhouette":"lavender crown/crest feathers with white facial plumage","texture":"layered soft feathers","hairline_or_pattern":"lavender crown transitions into white face; large lavender-white wings"},
    "base_tone":"lavender-purple + white",
    "unique_marks":["large layered wings","tail feathers","pink-white flower head ornaments"],
    "resting_expression":"bright cheerful smile"
  },
  "costume":{"identity_critical":["white/lavender jacket","blue-violet skirt","purple backpack","lavender-white sneakers"],"signature_accessories":["flower headpiece","flower motifs","gold hardware"],"signature_equipment":["backpack"],"materials":["layered feathers","woven jacket/skirt","decorative flower elements","leather-like straps","metallic gold hardware","rubber sneaker sole"]},
  "palette":["lavender","white","violet","blue-violet","soft pink","yellow-gold"]
},
"11": {
  "character_class":"ANIMAL","species_or_body_type":"RAM_BIPED",
  "head_face":{
    "shape":"rounded ram face with short white/cream muzzle and woolly cheek fur",
    "eyes":{"shape":"large rounded-almond","size":"large","spacing":"wide","angle":"calm","iris_color":"warm brown","distinctive":"dark rim and glossy highlights"},
    "brows":{"shape":"thick soft dark-brown arch","weight":"medium-heavy"},
    "nose_muzzle_beak":{"structure":"small dark ram nose on short cream muzzle","distinctive":"compact triangular-round nose"},
    "mouth_lips":{"shape":"small closed confident smile","distinctive":"subtle curved mouth"},
    "ears_horns_antennae":{"structure":"very large symmetrical dark-brown spiral horns with small pale ears beneath"},
    "hair_fur_feather":{"silhouette":"short white wool/fur with small crown tuft","texture":"soft dense woolly fur","hairline_or_pattern":"white head and cheek wool framed by dark horns"},
    "base_tone":"white / cream with dark-brown horns",
    "unique_marks":["massive curled horns","gold forehead emblem","small pale tail"],
    "resting_expression":"calm confident smile"
  },
  "costume":{"identity_critical":["cream hoodie","dark cropped cargo pants","dark backpack","navy-cream sneakers"],"signature_accessories":["gold forehead emblem","gold mountain/geometric hardware","dark paw/hoof gloves"],"signature_equipment":["backpack"],"materials":["soft wool/fur","woven hoodie","cargo textile","horn material","leather-like straps","metallic gold hardware","rubber sneaker sole"]},
  "palette":["white","cream","dark brown","navy","charcoal","gold"]
},
"12": {
  "character_class":"ANIMAL","species_or_body_type":"RABBIT_BIPED",
  "head_face":{
    "shape":"round rabbit face with soft pale muzzle",
    "eyes":{"shape":"very large rounded","size":"large","spacing":"wide","angle":"soft","iris_color":"coral-red / deep pink","distinctive":"dark upper lashes with glossy highlights; one-eye wink in source pose"},
    "brows":{"shape":"soft pale-pink arch","weight":"light"},
    "nose_muzzle_beak":{"structure":"tiny pale-pink rabbit nose on short muzzle","distinctive":"small centered nose"},
    "mouth_lips":{"shape":"wide open cheerful smile","distinctive":"small visible rabbit/fang-like tooth detail"},
    "ears_horns_antennae":{"structure":"very long pale rabbit ears with vivid pink inner panels"},
    "hair_fur_feather":{"silhouette":"very long voluminous pastel-pink wavy hair with curled side locks","texture":"silky layered hair over soft fur","hairline_or_pattern":"full layered pink fringe and long cascading curls"},
    "base_tone":"pale cream + saturated pastel pink hair",
    "unique_marks":["orange-gold flower hair clip","very long pink hair","long pink-lined ears","fluffy pale-pink tail"],
    "resting_expression":"playful cheerful smile"
  },
  "costume":{"identity_critical":["pink-white hoodie/jacket with floral motifs","navy pleated skirt","dark backpack","pink-white sneakers","white/pink socks"],"signature_accessories":["orange-gold flower hair clip","floral patches/charms"],"signature_equipment":["backpack"],"materials":["soft fur","silky hair","woven hoodie/jacket","pleated fabric","leather-like straps","metallic gold hardware","rubber sneaker sole"]},
  "palette":["pale cream","pastel pink","coral pink","navy","white","gold/orange flower accent"]
}
}

def fingerprint(card):
    payload={"visual_id":card["visual_id"],"source_sha256":card["identity_fingerprint"]["source_sha256"],"identity_lock":card["identity_lock"]}
    return hashlib.sha256(json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")).hexdigest()

reg=json.loads(REG.read_text(encoding="utf-8"))
paths={x["visual_id"]: ROOT/x["card_path"] for x in reg["roster"]}
for vid,t in TRAITS.items():
    p=paths[vid]
    card=json.loads(p.read_text(encoding="utf-8"))
    card["character_class"]=t["character_class"]
    card["species_or_body_type"]=t["species_or_body_type"]
    hf=card["identity_lock"]["head_face"]
    for k,v in t["head_face"].items(): hf[k]=v
    ce=card["identity_lock"]["costume_equipment"]
    ce["identity_critical"]=t["costume"]["identity_critical"]
    ce["signature_accessories"]=t["costume"]["signature_accessories"]
    ce["signature_equipment"]=t["costume"]["signature_equipment"]
    ce["materials"]=t["costume"]["materials"]
    card["identity_lock"]["color_material_palette"]=t["palette"]
    src=card["authority"]["approved_source_refs"][0]
    card["detail_anchors"].update({
      "front_face":src,"three_quarter_face":src,"eyes":src,"nose_muzzle_beak":src,"mouth":src,
      "hair_fur_feather":src,"skin_fur_texture":src,
      "limb_detail":card["turnaround_views"]["authority_registry"],
      "signature_prop_grip":src
    })
    card["backfill_status"]["fine_face_detail"]="BACKFILLED_FROM_APPROVED_SOURCE"
    card["backfill_status"]["color_material"]="BACKFILLED_SEMANTIC_FROM_APPROVED_SOURCE"
    card["identity_fingerprint"]["digest"]=fingerprint(card)
    card["identity_fingerprint"]["status"]="CORE_IDENTITY_FINGERPRINT_READY"
    p.write_text(json.dumps(card,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("PASS: Visual ID detail backfill 07-12 = 6/6")
