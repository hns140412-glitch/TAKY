import json, hashlib
from pathlib import Path

ROOT = Path(r"D:\Git PWA\TAKY\MASTER\CHARACTER_VISUAL_ID_CARDS")

TRAITS = {
"01_Dooby.json": {
  "character_class":"ANIMAL",
  "species_or_body_type":"CANINE_BIPED",
  "head_face":{
    "shape":"rounded canine head with broad cream muzzle/cheek mask",
    "eyes":{"shape":"very large rounded oval","size":"large","spacing":"wide","angle":"neutral-soft","iris_color":"deep brown with warm amber lower ring","distinctive":"large glossy highlights and dark rim"},
    "brows":{"shape":"soft arched","weight":"medium"},
    "nose_muzzle_beak":{"structure":"small dark canine nose over short cream muzzle","distinctive":"compact centered nose"},
    "mouth_lips":{"shape":"wide open cheerful mouth","distinctive":"small visible canine teeth in smiling pose"},
    "ears_horns_antennae":{"structure":"large upright triangular ears with pale-pink inner ear"},
    "hair_fur_feather":{"silhouette":"tan short fur with small swept forehead tufts","texture":"soft plush fur","hairline_or_pattern":"cream facial mask and muzzle; tan crown"},
    "base_tone":"warm tan + cream",
    "unique_marks":["cream muzzle/cheeks","cream tail tip"],
    "resting_expression":"bright open smile"
  },
  "costume":{
    "identity_critical":["blue-white explorer cap","cream varsity-style jacket","blue hoodie","dark cropped cargo pants","blue-white sneakers","dark explorer backpack"],
    "signature_accessories":["gold star hardware","mountain/star patches","dark paw gloves"],
    "signature_equipment":["explorer backpack"],
    "materials":["soft fur","woven jacket/hoodie","cargo textile","leather-like straps","metallic gold hardware","rubber sneaker sole"]
  },
  "palette":["warm tan fur","cream face/tail accents","royal blue","off-white","charcoal","gold hardware","dark brown straps"]
},
"02_Rory.json": {
  "character_class":"ANIMAL",
  "species_or_body_type":"RABBIT_BIPED",
  "head_face":{
    "shape":"round rabbit face with soft cream/white muzzle area",
    "eyes":{"shape":"very large rounded","size":"large","spacing":"wide","angle":"soft","iris_color":"pink-magenta gradient","distinctive":"dark upper lashes and bright glossy highlights"},
    "brows":{"shape":"soft slim arch","weight":"light"},
    "nose_muzzle_beak":{"structure":"tiny pink rabbit nose on short muzzle","distinctive":"small centered triangular-round nose"},
    "mouth_lips":{"shape":"small open smiling mouth","distinctive":"tiny visible front/fang-like tooth detail in source pose"},
    "ears_horns_antennae":{"structure":"very long upright white rabbit ears with broad pink inner panels"},
    "hair_fur_feather":{"silhouette":"soft wavy pastel-pink bob with curled crown tuft","texture":"silky layered hair over soft fur","hairline_or_pattern":"side-swept bangs and curled side locks"},
    "base_tone":"cream-white fur + pastel pink hair",
    "unique_marks":["gold star hair clip","long pink-lined ears","small white fluffy tail"],
    "resting_expression":"playful cheerful smile"
  },
  "costume":{
    "identity_critical":["cream/pink jacket","pink hoodie","navy pleated skirt","navy backpack","pink-white sneakers","white/pink striped socks"],
    "signature_accessories":["gold star hair clip","gold star charms","white pom-pom charm"],
    "signature_equipment":["backpack"],
    "materials":["soft fur","silky hair","woven hoodie/jacket","pleated fabric","leather-like straps","metallic gold hardware","rubber sneaker sole"]
  },
  "palette":["cream-white","pastel pink","navy","soft coral pink","gold","white"]
},
"03_Ink.json": {
  "character_class":"ANIMAL",
  "species_or_body_type":"FELINE_BIPED",
  "head_face":{
    "shape":"rounded feline head with tapered cream muzzle",
    "eyes":{"shape":"large almond-round","size":"large","spacing":"medium-wide","angle":"slightly focused","iris_color":"amber-gold","distinctive":"dark upper lash line and glossy highlights"},
    "brows":{"shape":"subtle fur-brow line","weight":"light"},
    "nose_muzzle_beak":{"structure":"small dark feline nose over cream muzzle","distinctive":"short centered muzzle"},
    "mouth_lips":{"shape":"small closed confident smile","distinctive":"subtle curved feline mouth"},
    "ears_horns_antennae":{"structure":"tall pointed feline ears with pale inner fur"},
    "hair_fur_feather":{"silhouette":"dark charcoal shaggy crown and cheek tufts","texture":"dense soft fur","hairline_or_pattern":"charcoal upper face with cream muzzle/cheeks"},
    "base_tone":"charcoal/dark brown + cream",
    "unique_marks":["cream muzzle/cheek mask","long dark tail with pale tip","gold-rim explorer goggles"],
    "resting_expression":"calm clever half-smile"
  },
  "costume":{
    "identity_critical":["gold-rim goggles on head","cream/blue jacket","blue hoodie","dark cargo pants","dark backpack","blue-white sneakers"],
    "signature_accessories":["gold star hardware","dark paw gloves"],
    "signature_equipment":["explorer goggles","backpack"],
    "materials":["dense fur","woven jacket/hoodie","cargo textile","leather-like straps","metallic gold hardware","rubber sneaker sole"]
  },
  "palette":["charcoal","deep brown","cream","royal blue","off-white","gold"]
},
"04_Nova.json": {
  "character_class":"ANIMAL",
  "species_or_body_type":"RODENT_BIPED",
  "head_face":{
    "shape":"round compact rodent head with broad cream muzzle/cheeks",
    "eyes":{"shape":"very large rounded","size":"large","spacing":"wide","angle":"soft","iris_color":"warm amber-brown","distinctive":"large glossy highlights; one-eye wink in source pose"},
    "brows":{"shape":"short dark arch","weight":"medium"},
    "nose_muzzle_beak":{"structure":"small rounded dark-brown nose on short muzzle","distinctive":"centered compact nose"},
    "mouth_lips":{"shape":"wide open cheerful smile","distinctive":"small visible front teeth/fangs in smiling pose"},
    "ears_horns_antennae":{"structure":"small rounded ears with pink inner ear"},
    "hair_fur_feather":{"silhouette":"short warm-brown plush fur with small crown tuft","texture":"soft dense plush fur","hairline_or_pattern":"cream face/muzzle mask against warm-brown crown"},
    "base_tone":"warm brown + cream",
    "unique_marks":["small rounded ears","cream facial mask","fluffy warm-brown tail"],
    "resting_expression":"energetic cheerful smile"
  },
  "costume":{
    "identity_critical":["gold-rim goggles","cream jacket","blue hoodie","dark cargo pants","dark backpack","blue-white sneakers"],
    "signature_accessories":["gold star charms","dark paw gloves"],
    "signature_equipment":["explorer goggles","backpack"],
    "materials":["plush fur","woven jacket/hoodie","cargo textile","leather-like straps","metallic gold hardware","rubber sneaker sole"]
  },
  "palette":["warm brown","cream","royal blue","charcoal","off-white","gold"]
},
"05_Take.json": {
  "character_class":"ANIMAL",
  "species_or_body_type":"PANDA_BIPED",
  "head_face":{
    "shape":"round panda head with broad white muzzle/cheeks",
    "eyes":{"shape":"large rounded","size":"large","spacing":"wide","angle":"soft","iris_color":"deep brown with warm amber ring","distinctive":"black panda eye patches frame glossy eyes"},
    "brows":{"shape":"short curved black brow marks","weight":"medium"},
    "nose_muzzle_beak":{"structure":"small black panda nose on white muzzle","distinctive":"compact rounded-triangular nose"},
    "mouth_lips":{"shape":"open friendly smile","distinctive":"rounded smiling mouth"},
    "ears_horns_antennae":{"structure":"round black panda ears"},
    "hair_fur_feather":{"silhouette":"smooth plush panda fur with tiny crown tuft","texture":"soft dense plush fur","hairline_or_pattern":"white head with black ears and symmetrical black eye patches"},
    "base_tone":"white + black",
    "unique_marks":["large black eye patches","round black ears"],
    "resting_expression":"warm friendly smile"
  },
  "costume":{
    "identity_critical":["blue hoodie","cream jacket","dark cargo pants","dark backpack","blue-white sneakers"],
    "signature_accessories":["gold star hardware","dark paw gloves"],
    "signature_equipment":["backpack"],
    "materials":["plush fur","woven hoodie/jacket","cargo textile","leather-like straps","metallic gold hardware","rubber sneaker sole"]
  },
  "palette":["white","black","royal blue","charcoal","cream","gold"]
},
"06_Zero.json": {
  "character_class":"ANIMAL",
  "species_or_body_type":"AVIAN_PENGUIN_BIPED",
  "head_face":{
    "shape":"round penguin head with white facial field",
    "eyes":{"shape":"large rounded","size":"large","spacing":"wide","angle":"soft","iris_color":"deep brown with warm gold lower tone","distinctive":"dark upper lash line; one-eye wink in source pose"},
    "brows":{"shape":"not separately pronounced; eye expression carries brow cue","weight":"minimal"},
    "nose_muzzle_beak":{"structure":"short compact orange-yellow penguin beak","distinctive":"small wedge beak centered in white face"},
    "mouth_lips":{"shape":"open cheerful beak-mouth","distinctive":"pink mouth interior visible in source pose"},
    "ears_horns_antennae":{"structure":"none; head silhouette defined by cap/headphones"},
    "hair_fur_feather":{"silhouette":"smooth dark charcoal crown/feather cap with white face field","texture":"soft plush feather/fur-like surface","hairline_or_pattern":"dark crown sweeping around white face"},
    "base_tone":"charcoal + white + orange-yellow beak",
    "unique_marks":["white facial field","dark crown","orange-yellow beak","wing/flipper arms"],
    "resting_expression":"playful cheerful smile"
  },
  "costume":{
    "identity_critical":["blue-white cap","large black/gold headphones","blue hoodie","cream jacket","dark lower outfit","dark backpack","blue-white sneakers"],
    "signature_accessories":["large headphones","gold star hardware"],
    "signature_equipment":["headphones","backpack"],
    "materials":["soft feather/fur-like surface","woven cap/hoodie/jacket","leather-like straps","metallic gold hardware","rubber sneaker sole"]
  },
  "palette":["charcoal","white","royal blue","cream","gold","orange-yellow beak"]
}
}

def fingerprint(card):
    payload={
      "visual_id":card["visual_id"],
      "source_sha256":card["identity_fingerprint"]["source_sha256"],
      "identity_lock":card["identity_lock"],
    }
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",",":")).encode("utf-8")).hexdigest()

for name, t in TRAITS.items():
    p=ROOT/name
    card=json.loads(p.read_text(encoding="utf-8"))
    card["character_class"]=t["character_class"]
    card["species_or_body_type"]=t["species_or_body_type"]
    hf=card["identity_lock"]["head_face"]
    for k,v in t["head_face"].items():
        hf[k]=v
    ce=card["identity_lock"]["costume_equipment"]
    ce["identity_critical"]=t["costume"]["identity_critical"]
    ce["signature_accessories"]=t["costume"]["signature_accessories"]
    ce["signature_equipment"]=t["costume"]["signature_equipment"]
    ce["materials"]=t["costume"]["materials"]
    card["identity_lock"]["color_material_palette"]=t["palette"]
    src=card["authority"]["approved_source_refs"][0]
    card["detail_anchors"].update({
      "front_face":src,
      "three_quarter_face":src,
      "eyes":src,
      "nose_muzzle_beak":src,
      "mouth":src,
      "hair_fur_feather":src,
      "skin_fur_texture":src,
      "limb_detail":card["turnaround_views"]["authority_registry"],
      "signature_prop_grip":src
    })
    card["backfill_status"]["fine_face_detail"]="BACKFILLED_FROM_APPROVED_SOURCE"
    card["backfill_status"]["color_material"]="BACKFILLED_SEMANTIC_FROM_APPROVED_SOURCE"
    card["identity_fingerprint"]["digest"]=fingerprint(card)
    card["identity_fingerprint"]["status"]="CORE_IDENTITY_FINGERPRINT_READY"
    p.write_text(json.dumps(card,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

print("PASS: Core6 approved-source Visual ID detail backfill 6/6")
