"""
milestones_data.py

Source: "Developmental milestones and the Early Years Learning Framework
and the National Quality Standards" (EYLF Practice Based Resources,
Community Child Care Co-operative Ltd NSW).

This holds the OBSERVE bullet points from that document, verbatim, so the
rest of the app grounds its generated content in the actual reference
instead of the AI's own general knowledge.

Band mapping — IMPORTANT CAVEAT:
The source document provides these bands: Birth-4 months, 4-8 months,
8-12 months, 1-2 years, 2-3 years, and ONE combined "3 to 5 years" band.
It does NOT split 3-5 into 3-4 and 4-5 separately.

To offer 5 dropdown bands (0-1, 1-2, 2-3, 3-4, 4-5) as requested:
- 0-1 years = the three infant bands merged (Birth-4mo + 4-8mo + 8-12mo)
- 1-2 years = sourced directly
- 2-3 years = sourced directly
- 3-4 years = drawn from the combined "3 to 5 years" section
- 4-5 years = drawn from the SAME combined "3 to 5 years" section

Since 3-4 and 4-5 share one source list, anywhere the app needs to treat
them differently (e.g. worksheet difficulty), that's an interpretation of
the document's own emerging-to-advanced ordering, not a second source —
flagged here so it's never confused with a literal document split.
"""

AGE_BANDS = ["0-1 years", "1-2 years", "2-3 years", "3-4 years", "4-5 years"]

# The literal bullet points, by band, by developmental area.
MILESTONES = {
    "0-1 years": {
        "physical": [
            "moves whole body, squirms, arms wave, legs move up and down",
            "startle reflex when placed unwrapped on flat surface / when hears loud noise",
            "head turns to side when cheek touched; sucking motions with mouth (seeking nipple)",
            "responds to gentle touching, cuddling, rocking",
            "able to lift head and chest when laying on stomach; begins to roll from side to side",
            "starts reaching to swipe at dangling objects; able to grasp object put into hands",
            "plays with feet and toes; makes effort to sit alone, but needs hand support",
            "makes crawling movements when lying on stomach; rolls from back to stomach",
            "reaches for and grasps objects, using one hand to grasp",
            "crawling movements using both hands and feet; able to take weight on feet when standing",
            "pulls self to standing position when hands held; sits without support",
            "stands by pulling self up using furniture; stepping movements around furniture",
            "transfers objects from hand to hand; picks up and pokes small objects with thumb and finger",
            "crawls; mature crawling (quick and fluent); may stand alone momentarily",
            "uses hands to feed self; rolls ball and crawls to retrieve",
        ],
        "social": [
            "smiles and laughs; makes eye contact when held about 20cm from adult's face",
            "alert and preoccupied with faces; moves head to sound of voices",
            "reacts with arousal, attention or approach to presence of another baby or young child",
            "responds to own name; recognises familiar people and stretches arms to be picked up",
            "shows definite anxiety or wariness at appearance of strangers",
        ],
        "emotional": [
            "bonding; cries (peaks about six to eight weeks) and levels off about 12-14 weeks",
            "cries when hungry or uncomfortable and usually stops when held",
            "shows excitement as parent prepared to feed",
            "laughs, especially in social interactions; may soothe self by sucking thumb or dummy",
            "begins to show wariness of strangers; may fret when parent leaves the room",
            "actively seeks to be next to parent or principal caregiver",
            "shows signs of anxiety or stress if parent goes away",
            "shows signs of empathy to distress of another (but often soothes self)",
        ],
        "cognitive": [
            "looks toward direction of sound; eyes track slow moving target for brief period",
            "looks at edges, patterns with light/dark contrast and faces",
            "imitates adult tongue movements when being held/talked to; learns through sensory experiences",
            "swipes at dangling objects; shakes and stares at toy placed in hand",
            "repeats accidentally caused actions that are interesting",
            "enjoys games such as peek-a-boo or pat-a-cake; will search for partly hidden object",
            "able to coordinate looking, hearing and touching; enjoys banging objects, scrunching paper",
            "moves obstacle to get at desired toy; bangs two objects held in hands together",
            "makes gestures to communicate/symbolise objects, e.g. points to something they want",
            "understands gestures / responds to 'bye bye'; notices difference and shows surprise",
        ],
        "language": [
            "expresses needs by crying; when content makes small throaty noises",
            "soothed by sound of voice or by low rhythmic sounds; may start to copy sounds; coos and gurgles",
            "babbles and repeats sounds; makes talking sounds in response to others talking",
            "smiles and babbles at own image in mirror; responds to own name",
            "says words like 'dada' or 'mama'; waves goodbye; imitates hand clapping",
            "enjoys finger-rhymes; shouts to attract attention",
            "vocalises loudly using most vowels and consonants - sounding like conversation",
        ],
        "seek_advice_if": [
            "is floppy or stiff; cries a lot; arches back",
            "is not responding to sounds or familiar faces",
            "is not showing interest or responding when played with",
            "is not feeding as expected / not learning to eat solids",
            "is not starting to make sounds or babbling",
            "is not beginning to sit, crawl, or pull to stand",
        ],
    },
    "1-2 years": {
        "physical": [
            "walks, climbs and runs; takes two to three steps without support, legs wide, hands up for balance",
            "crawls up steps; dances in place to music; climbs onto chair",
            "kicks and throws a ball; feeds themselves; begins to run (hurried walk)",
            "scribbles with pencil or crayon held in fist",
            "turns pages of book, two or three pages at a time",
            "rolls large ball, using both hands and arms; finger feeds efficiently",
            "begins to walk alone in a 'tottering way', with frequent falls; squats to pick up an object",
            "reverts to crawling if in a hurry; can drink from a cup; tries to use spoon/fork",
        ],
        "social": [
            "begins to cooperate when playing",
            "may play alongside other toddlers, doing what they do but without seeming to interact (parallel play)",
            "curious and energetic, but depends on adult presence for reassurance",
        ],
        "emotional": [
            "may show anxiety when separating from significant people in their lives",
            "seeks comfort when upset or afraid",
            "takes cue from parent/principal carer regarding attitude to a stranger",
            "may 'lose control' of self when tired or frustrated",
            "assists another in distress by patting, making sympathetic noises or offering material objects",
        ],
        "cognitive": [
            "repeats actions that lead to interesting/predictable results, e.g. bangs spoon on saucepan",
            "points to objects when named; knows some body parts; points to body parts in a game",
            "recognises self in photo or mirror",
            "mimics household activities, e.g. bathing baby, sweeping floor",
            "spends a lot of time exploring/manipulating objects, putting in mouth, shaking, banging",
            "stacks and knocks over items; selects games and puts them away",
            "calls self by name, uses 'I', 'mine', 'I do it myself'; will search for hidden toys",
        ],
        "language": [
            "comprehends and follows simple questions/commands; says first name",
            "says many words (mostly naming words)",
            "begins to use one to two word sentences, e.g. 'want milk'",
            "reciprocal imitation of another toddler: will imitate each other's actions",
            "enjoys rhymes and songs",
        ],
        "seek_advice_if": [
            "is not using words or actions to communicate such as waving or raising arms to be lifted",
            "is not wanting to move around",
            "is not responding to others or seeking attention of familiar people",
        ],
    },
    "2-3 years": {
        "physical": [
            "walks, runs, climbs, kicks and jumps easily; uses steps one at a time",
            "squats to play and rises without using hands; catches ball rolled to him/her",
            "walks into a ball to kick it; jumps from low step or over low objects",
            "attempts to balance on one foot; avoids obstacles; able to open doors; stops readily",
            "moves about moving to music; turns pages one at a time",
            "holds crayon with fingers; uses a pencil to draw or scribble in circles and lines",
            "gets dressed with help; self-feeds using utensils and a cup",
        ],
        "social": [
            "plays with other children; simple make believe play",
            "may prefer same sex playmates and toys; unlikely to share toys without protest",
        ],
        "emotional": [
            "shows strong attachment to a parent (or main family carer)",
            "shows distress and protest when they leave and wants that person to do things for them",
            "begins to show guilt or remorse for misdeeds",
            "may be less likely to willingly share toys with peers; demands adult attention",
        ],
        "cognitive": [
            "builds tower of five to seven objects; lines up objects in 'train' fashion",
            "recognises and identifies common objects and pictures by pointing",
            "enjoys playing with sand, water, dough; explores what these materials can do more than making things",
            "uses symbolic play, e.g. use a block as a car",
            "shows knowledge of gender-role stereotypes; identifies picture as a boy or girl",
            "engages in making believe and pretend play",
            "begins to count with numbers; recognises similarities and differences",
            "imitates rhythms and animal movements",
            "becoming aware of space through physical activity; can follow two or more directions",
        ],
        "language": [
            "uses two or three words together, e.g. 'go potty now'",
            "'explosion' of vocabulary and use of correct grammatical forms of language",
            "refers to self by name and often says 'mine'; asks lots of questions",
            "uses pronouns and prepositions, simple sentences and phrases; labels own gender",
            "copies words and actions; makes music, sings and dances; likes listening to stories and books",
        ],
        "seek_advice_if": [
            "is not interested in playing; is falling a lot; finds it hard to use small objects",
            "is not understanding simple instructions; not using many words; not joining words in meaningful phrases",
            "is not interested in food or in others",
        ],
    },
    "3-5 years": {  # shared source for both "3-4 years" and "4-5 years" bands
        "physical": [
            "dresses and undresses with little help; hops, jumps and runs with ease",
            "climbs steps with alternating feet; gallops and skips by leading with one foot",
            "transfers weight forward to throw ball; attempts to catch ball with hands",
            "climbs playground equipment with increasing agility",
            "holds crayon/pencil etc. between thumb and first two fingers; exhibits hand preference",
            "imitates variety of shapes in drawing, e.g. circles",
            "independently cuts paper with scissors",
            "toilets themselves; feeds self with minimum spills; dresses/undresses with minimal assistance",
            "walks and runs more smoothly; enjoys learning simple rhythm and movement routines",
            "develops ability to toilet train at night",
        ],
        "social": [
            "enjoys playing with other children; may have a particular friend",
            "shares, smiles and cooperates with peers; jointly manipulates objects with one or two other peers",
            "develops independence and social skills they will use at preschool and school",
        ],
        "emotional": [
            "understands when someone is hurt and comforts them",
            "attains gender stability; may show stronger preference for same-sex playmates",
            "may show bouts of aggression with peers",
            "likes to give and receive affection from parents; may praise themselves and be boastful",
        ],
        "cognitive": [
            "understands opposites (e.g. big/little) and positional words (middle, end)",
            "uses objects and materials to build or construct things, e.g. block tower, puzzle, clay, sand and water",
            "builds tower eight to ten blocks; answers simple questions; counts five to ten things",
            "has a longer attention span; talks to self during play to help guide what he/she does",
            "follows simple instructions; follows simple rules and enjoys helping",
            "may write some numbers and letters",
            "engages in dramatic play, taking on pretend character roles; recalls events correctly",
            "counts by rote, having memorised numbers",
            "touches objects to count - starting to understand relationship between numbers and objects",
            "can recount a recent story",
            "copies letters and may write some unprompted",
            "can match and name some colours",
        ],
        "language": [
            "speaks in sentences and uses many different words; answers simple questions; asks many questions",
            "tells stories; talks constantly; enjoys experimenting with new words",
            "uses adult forms of speech; takes part in conversations",
            "enjoys jokes, rhymes and stories; will assert self with words",
        ],
        "seek_advice_if": [
            "is not understood by others; has speech fluency problems or stammering",
            "is not playing with other children; not able to have a conversation",
            "is not able to go to the toilet or wash him/herself",
        ],
    },
}

# Which source band each dropdown band actually pulls from (see caveat above)
AGE_BAND_SOURCE = {
    "0-1 years": "0-1 years",
    "1-2 years": "1-2 years",
    "2-3 years": "2-3 years",
    "3-4 years": "3-5 years",
    "4-5 years": "3-5 years",
}


def get_milestones(age_band: str) -> dict:
    return MILESTONES[AGE_BAND_SOURCE[age_band]]


def milestones_summary_text(age_band: str, areas=None) -> str:
    """Compact bullet-point grounding text for AI prompts — the actual
    document content, not a paraphrase, so generated activities stay
    anchored to real observed behaviours for this age."""
    data = get_milestones(age_band)
    areas = areas or ["physical", "social", "emotional", "cognitive", "language"]
    lines = []
    for area in areas:
        items = data.get(area, [])
        if items:
            lines.append(f"{area.capitalize()}: " + " | ".join(items))
    return "\n".join(lines)