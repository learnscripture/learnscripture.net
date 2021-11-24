# Some proper tests are in learnscripture.tests
# These are just for experimental work at the moment and aren't run automatically.

import random
import resource
import timeit

from bibleverses.books import get_bible_books
from bibleverses.languages import LANGUAGE_CODE_EN

from . import serverlogging  # noqa: F401
from .constants import ALL_TEXT, BIBLE_BOOK_GROUPS, THESAURUS_ANALYSIS
from .generators import SuggestionGenerator
from .storage import AnalysisStorage
from .trainingtexts import BibleTrainingTexts, CatechismTrainingTexts

try:
    import pympler.asizeof
except (ImportError, AttributeError):  # PyPy
    pympler = None


_last_mem_usage = 0

suffixes = ["b", "Kb", "Mb", "Gb", "Tb", "Pb"]


def nice_mem_units(nbytes):
    i = 0
    while nbytes >= 1024 and i < len(suffixes) - 1:
        nbytes /= 1024.0
        i += 1
    f = (f"{nbytes:.2f}").rstrip("0").rstrip(".")
    return f"{f} {suffixes[i]}"


def print_mem_usage(comment):
    global _last_mem_usage
    new_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    print(comment)
    print("Memory: " + nice_mem_units(new_usage))
    diff = new_usage - _last_mem_usage
    print("Difference: " + nice_mem_units(diff))
    _last_mem_usage = new_usage


def print_object_usage(object_name, obj):
    if pympler is None:
        return
    print(object_name + ": " + nice_mem_units(pympler.asizeof.asizeof(obj)))


def test_thesaurus_memory():
    print_mem_usage("Start")
    from .storage import AnalysisStorage

    s = AnalysisStorage()
    print_mem_usage("After creating storage")
    thesaurus = s.load_analysis(THESAURUS_ANALYSIS, [("NET", ALL_TEXT)])
    print_mem_usage("After loading NET thesaurus")
    print_object_usage("Thesaurus", thesaurus)


def generators_for_bible_text(storage, text_slug):
    """
    Returns a dictionary with keys (text_slug, book name)
    and values as a list of strategies
    """
    retval = {}
    for book_group in BIBLE_BOOK_GROUPS:
        generator = SuggestionGenerator(BibleTrainingTexts(text_slug=text_slug, books=book_group))
        # This same generator can be used for each Bible book:
        for book in book_group:
            retval[text_slug, book] = generator
    return retval


def generators_for_catechism_text(storage, text_slug):
    return {(text_slug, ALL_TEXT): SuggestionGenerator(CatechismTrainingTexts(text_slug=text_slug))}


def test_server_memory_usage():
    print_mem_usage("Start")
    storage = AnalysisStorage()
    print_mem_usage("After creating storage")

    bible_versions = ["NET"]
    catechism_versions = ["WSC", "BC1695"]
    all_generators = {}
    for slug in bible_versions:
        all_generators.update(generators_for_bible_text(storage, slug))
    for slug in catechism_versions:
        all_generators.update(generators_for_catechism_text(storage, slug))

    print_mem_usage("After creating strategies")

    for strategies in all_generators.values():
        strategies.load_data(storage)

    print_mem_usage("After loading strategies")
    TEXT = "For God so loved the world, he gave his only begotten Son"

    for generator in all_generators.values():
        generator.suggestions_for_text(TEXT)
    print_mem_usage("After using all strategies")
    print_object_usage("storage", storage)
    print_object_usage("generators", all_generators)


def test_suggestion_speed():
    storage = AnalysisStorage()
    generators = generators_for_bible_text(storage, "NET")
    for g in generators.values():
        g.load_data(storage)

    COUNT = 5

    def f():
        for t in TEXTS:
            book = random.choice(get_bible_books(LANGUAGE_CODE_EN))
            generator = generators["NET", book]
            generator.suggestions_for_text(t)

    print("Time per text: " + str(timeit.timeit(f, number=COUNT) / (len(TEXTS) * COUNT)))


TEXTS = [
    "This is the law of the diseased infection in the garment of wool or linen, "
    "or the warp or woof, or any article of leather, for pronouncing it clean or "
    "unclean. ",
    "She went up and laid him down on the prophet's bed. She shut the door behind " "her and left. ",
    "so that you may welcome her in the Lord in a way worthy of the saints and "
    "provide her with whatever help she may need from you, for she has been a "
    "great help to many, including me. ",
    "Then all the men of Judah and Jerusalem returned joyfully to Jerusalem with "
    "Jehoshaphat leading them; the LORD had given them reason to rejoice over "
    "their enemies. ",
    "At that time, when Jeroboam had left Jerusalem, the prophet Ahijah the "
    "Shilonite met him on the road; the two of them were alone in the open "
    "country. Ahijah was wearing a brand new robe,",
    "For the ground that has soaked up the rain that frequently falls on it and "
    "yields useful vegetation for those who tend it receives a blessing from "
    "God. ",
    "He followed in the footsteps of the kings of Israel; he also made images of " "the Baals. ",
    "After this happened, Jeroboam still did not change his evil ways; he "
    "continued to appoint common people as priests at the high places. Anyone who "
    "wanted the job he consecrated as a priest. ",
    "I will lay waste your cities; and you will become desolate. Then you will " "know that I am the LORD!",
    "They will steal your wealth and loot your merchandise. They will tear down "
    "your walls and destroy your luxurious homes. Your stones, your trees, and "
    "your soil he will throw into the water. ",
    "Awake, my soul! Awake, O stringed instrument and harp! I will wake up at " "dawn!",
    "and the stars in the sky fell to the earth like a fig tree dropping its "
    "unripe figs when shaken by a fierce wind. ",
    "testifying to both Jews and Greeks about repentance toward God and faith in " "our Lord Jesus. ",
    "because I have given them the words you have given me. They accepted them "
    "and really understand that I came from you, and they believed that you sent "
    "me. ",
    "By the multitude of your iniquities, through the sinfulness of your trade, "
    "you desecrated your sanctuaries. So I drew fire out from within you; it "
    "consumed you, and I turned you to ashes on the earth before the eyes of all "
    "who saw you. ",
    '"Of what importance to me are your many sacrifices?" says the LORD. "I am '
    "stuffed with burnt sacrifices of rams and the fat from steers. The blood of "
    "bulls, lambs, and goats I do not want. ",
    "Deliver me from my distress; rescue me from my suffering!",
    "One of you makes a thousand run away, for the LORD your God fights for you " "as he promised you he would. ",
    "Are not my days few? Cease, then, and leave me alone, that I may find a " "little comfort,",
    "Then the LORD became zealous for his land; he had compassion on his people. ",
    "I will multiply the fruit of the trees and the produce of the fields, so "
    "that you will never again suffer the disgrace of famine among the nations. ",
    "You should make images of the sores and images of the mice that are "
    "destroying the land. You should honor the God of Israel. Perhaps he will "
    "release his grip on you, your gods, and your land. ",
    'Samson said to her, "If they tie me up with seven fresh bowstrings that have '
    'not been dried, I will become weak and be just like any other man."',
    "As she continued praying to the LORD, Eli was watching her mouth. ",
    "Johanan was the father of Azariah, who served as a priest in the temple " "Solomon built in Jerusalem. ",
    "If he designated her for his son, then he will deal with her according to " "the customary rights of daughters. ",
    "When they arrest you and hand you over for trial, do not worry about what to "
    "speak. But say whatever is given you at that time, for it is not you "
    "speaking, but the Holy Spirit. ",
    'So Jesus replied, "My teaching is not from me, but from the one who sent ' "me. ",
    "Then the servant took ten of his master's camels and departed with all kinds "
    "of gifts from his master at his disposal. He journeyed to the region of Aram "
    "Naharaim and the city of Nahor. ",
    "Then Abraham bowed down with his face to the ground and laughed as he said "
    'to himself, "Can a son be born to a man who is a hundred years old? Can '
    'Sarah bear a child at the age of ninety?"',
    "The rest of the events of Menahem's reign, including all his "
    "accomplishments, are recorded in the scroll called the Annals of the Kings "
    "of Israel. ",
    "Dark clouds surround him; equity and justice are the foundation of his " "throne. ",
    "If he designated her for his son, then he will deal with her according to " "the customary rights of daughters. ",
    'Simon Peter told them, "I am going fishing." "We will go with you," they '
    "replied. They went out and got into the boat, but that night they caught "
    "nothing. ",
    "At that time they sacrificed to the LORD some of the plunder they had "
    "brought back, including 700 head of cattle and 7,000 sheep. ",
    '"Are you the one who is to come, or should we look for another?"',
    '"Blessed are the peacemakers, for they will be called the children of God. ',
    "When David had settled into his palace, he said to Nathan the prophet, "
    "\"Look, I am living in a palace made from cedar, while the ark of the LORD's "
    'covenant is under a tent."',
    "Now we have not received the spirit of the world, but the Spirit who is from "
    "God, so that we may know the things that are freely given to us by God. ",
    "Get up, make your way across Wadi Arnon. Look! I have already delivered over "
    "to you Sihon the Amorite, king of Heshbon, and his land. Go ahead! Take it! "
    "Engage him in war!",
    "So Jacob came back to his father Isaac in Mamre, to Kiriath Arba (that is, "
    "Hebron), where Abraham and Isaac had stayed. ",
    "The Israelites cried out for help to the LORD, because Sisera had nine "
    "hundred chariots with iron-rimmed wheels, and he cruelly oppressed the "
    "Israelites for twenty years. ",
    'While they were going down to the edge of town, Samuel said to Saul, "Tell '
    'the servant to go on ahead of us." So he did. Samuel then said, "You remain '
    "here awhile, so I can inform you of God's message.\"",
    "Without being weak in faith, he considered his own body as dead (because he "
    "was about one hundred years old) and the deadness of Sarah's womb. ",
    "Now I mean that the heir, as long as he is a minor, is no different from a "
    "slave, though he is the owner of everything. ",
    "Your servant Joab did this so as to change this situation. But my lord has "
    "wisdom like that of the angel of God, and knows everything that is happening "
    'in the land."',
    "A fool will no longer be called honorable; a deceiver will no longer be " "called principled. ",
    "This is the account of Isaac, the son of Abraham. Abraham became the father " "of Isaac. ",
    "and he said to them, \"Thus says the Lord, the God of Israel, 'Each man "
    "fasten his sword on his side, and go back and forth from entrance to "
    "entrance throughout the camp, and each one kill his brother, his friend, and "
    "his neighbor.'\"",
    "Then you will succeed, if you carefully obey the rules and regulations which "
    "the LORD ordered Moses to give to Israel. Be strong and brave! Don't be "
    "afraid and don't panic!",
    'I heard, but I did not understand. So I said, "Sir, what will happen after ' 'these things?"',
    "The clods of the torrent valley are sweet to him; behind him everybody "
    "follows in procession, and before him goes a countless throng. ",
    'The LORD said to me, "What do you see, Jeremiah?" I answered, "I see figs. '
    "The good ones look very good. But the bad ones look very bad, so bad that "
    'they cannot be eaten."',
    "Both the apostles and the elders met together to deliberate about this " "matter. ",
    "until the Ancient of Days arrived and judgment was rendered in favor of the "
    "holy ones of the Most High. Then the time came for the holy ones to take "
    "possession of the kingdom. ",
    "A thoroughfare will be there - it will be called the Way of Holiness. The "
    "unclean will not travel on it; it is reserved for those authorized to use it "
    "- fools will not stray into it. ",
    "a nation of stern appearance that will have no regard for the elderly or " "pity for the young. ",
    "But he denied it: \"I don't even understand what you're talking about!\" "
    "Then he went out to the gateway, and a rooster crowed. ",
    '"We can\'t," they said, "until all the flocks are gathered and the stone is '
    'rolled off the mouth of the well. Then we water the sheep."',
    "the tabernacle with its tent, its covering, its clasps, its frames, its " "crossbars, its posts, and its bases;",
    "Is this really your boisterous city whose origins are in the distant past, "
    "and whose feet led her to a distant land to reside?",
    "If he refuses to listen to them, tell it to the church. If he refuses to "
    "listen to the church, treat him like a Gentile or a tax collector. ",
    '"If you lend money to any of my people who are needy among you, do not be '
    "like a moneylender to him; do not charge him interest. ",
    "The son of Gershom: Shebuel the oldest. ",
    "The LORD answered Elijah's prayer; the boy's breath returned to him and he " "lived. ",
    "Now on the first day of the feast of Unleavened Bread, when the Passover "
    "lamb is sacrificed, Jesus' disciples said to him, \"Where do you want us to "
    'prepare for you to eat the Passover?"',
    "When the centurion heard this, he went to the commanding officer and "
    'reported it, saying, "What are you about to do? For this man is a Roman '
    'citizen."',
    'He said to me, "You are my servant, Israel, through whom I will reveal my ' 'splendor."',
    "So a treaty curse devours the earth; its inhabitants pay for their guilt. "
    "This is why the inhabitants of the earth disappear, and are reduced to just "
    "a handful of people. ",
    "But as the church submits to Christ, so also wives should submit to their " "husbands in everything. ",
    '"I, Jesus, have sent my angel to testify to you about these things for the '
    "churches. I am the root and the descendant of David, the bright morning "
    'star!"',
    "By his power he stills the sea; by his wisdom he cut Rahab the great sea " "monster to pieces. ",
    "Alammelech, Amad, and Mishal. Their border touched Carmel to the west and " "Shihor Libnath. ",
    "Pay attention to me and answer me! I am so upset and distressed, I am beside " "myself,",
    'But "when the kindness of God our Savior and his love for mankind appeared,',
    "The one who loves his life destroys it, and the one who hates his life in "
    "this world guards it for eternal life. ",
    "When he has brought all his own sheep out, he goes ahead of them, and the "
    "sheep follow him because they recognize his voice. ",
    'Then Jesus said to them, "I tell you the truth, there is no one who has left '
    "home or wife or brothers or parents or children for the sake of God's "
    "kingdom",
    "Confirm to your servant your promise, which you made to the one who honors " "you. ",
    "Solomon began building the LORD's temple in Jerusalem on Mount Moriah, where "
    "the LORD had appeared to his father David. This was the place that David "
    "prepared at the threshing floor of Ornan the Jebusite. ",
    'Jesus said to them, "I will ask you one question. Answer me and I will tell '
    "you by what authority I do these things:",
    "When Joseph came home, they presented him with the gifts they had brought "
    "inside, and they bowed down to the ground before him. ",
    "From the tribe of Benjamin they assigned Gibeon, Geba,",
    "Beth Zur, Soco, Adullam,",
    'They sent to him their disciples along with the Herodians, saying, "Teacher, '
    "we know that you are truthful, and teach the way of God in accordance with "
    "the truth. You do not court anyone's favor because you show no partiality. ",
    "it is you, O king! For you have become great and strong. Your greatness is "
    "such that it reaches to heaven, and your authority to the ends of the "
    "earth. ",
    "Therefore he had to be made like his brothers and sisters in every respect, "
    "so that he could become a merciful and faithful high priest in things "
    "relating to God, to make atonement for the sins of the people. ",
    "However, I will first tell you what is written in a dependable book. (There "
    "is no one who strengthens me against these princes, except Michael your "
    "prince. ",
    "Make the work harder for the men so they will keep at it and pay no " 'attention to lying words!"',
    "For this reason I carefully follow all your precepts. I hate all deceitful " "actions. ",
    "'I see him, but not now; I behold him, but not close at hand. A star will "
    "march forth out of Jacob, and a scepter will rise out of Israel. He will "
    "crush the skulls of Moab, and the heads of all the sons of Sheth. ",
    'Then the seventy-two returned with joy, saying, "Lord, even the demons ' 'submit to us in your name!"',
    "In him was life, and the life was the light of mankind. ",
    "While they were perplexed about this, suddenly two men stood beside them in " "dazzling attire. ",
    "Now this matter arose because of the false brothers with false pretenses who "
    "slipped in unnoticed to spy on our freedom that we have in Christ Jesus, to "
    "make us slaves. ",
    "Instruct these people as follows: 'You are about to cross the border of your "
    "relatives the descendants of Esau, who inhabit Seir. They will be afraid of "
    "you, so watch yourselves carefully. ",
    "Those that entered were male and female, just as God commanded him. Then the " "LORD shut him in. ",
    "Do you have an arm as powerful as God's, and can you thunder with a voice " "like his?",
    "And sons were also born to Shem (the older brother of Japheth), the father " "of all the sons of Eber. ",
    'His servants said to him, "What is this that you have done? While the child '
    "was still alive, you fasted and wept. Once the child was dead you got up and "
    'ate food!"',
]
