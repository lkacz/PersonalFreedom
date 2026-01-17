"""
Weight Control Tips for Rodent Squad entities.

100 practical tips (real advice) when you have the telepathic White Mouse Archimedes.
100 "rodent language" tips (squeaks/nonsense) before you have the telepathic translator.

The catch: Without scientist_009 (White Mouse Archimedes, normal or exceptional),
you can't understand rodent language, so tips are presented as adorable squeaks.
Once you collect Archimedes, you can understand the Rodent Squad's wisdom!
"""

from typing import Tuple

# =============================================================================
# RODENT LANGUAGE TIPS - Before you have the telepathic White Mouse Archimedes
# (Adorable squeaks that make no sense but are still worth a coin!)
# =============================================================================

RODENT_LANGUAGE_TIPS = [
    ("Squee-rrip, chik-chik—prrrt. (plants both paws on the food bowl, then points its nose at you like 'you know what this means') Wheek… snorf-snorf—pip! (does a tiny head-tilt, waiting for your response)", "🐭"),
    ("Chrrt-chrrt, eep-EEP—skrrk! (stands upright to 'lecture,' then forgets the point mid-sentence) Pip pip… wheeeep. (tail swishes in slow punctuation like a stern professor)", "🐭"),
    ("Skrit-skrit—bip! squeeet-squeeet. (drags a seed three centimeters, as if demonstrating 'progress') Prrr… chrrrk. (pauses to groom one whisker, then resumes the 'presentation')", "🐭"),
    ("Eep-eep, prrrt—chik! (leans forward, sniffing the air like it's reading invisible text) Wheek-wheek… pip. (taps the floor twice, as if underlining a key idea)", "🐭"),
    ("Squee… squee… CHRRT! (freezes dramatically, then resumes with renewed confidence) Skrrk—pip pip—wheep. (nudges an imaginary chart with its nose, very official)", "🐭"),
    ("Bip-bip, chrrt! prrip-prrip. (scurries in a tiny circle like 'step 1, step 2, step 3') Wheeeek… eep. (stares at you as if you missed the obvious part)", "🐭"),
    ("Chik-chik, skrrt-skrrt—SQUEE! (climbs one centimeter up a wall and acts like it conquered Everest) Prrr… pip. (slow blink of smug satisfaction)", "🐭"),
    ("Wheep-wheep, snorf—chrrrk. (sniffs your shoe like it contains the secret) Eep! pip pip. (backs away politely, as if the secret was too powerful)", "🐭"),
    ("Skrrk! chrrt-chrrt—bip. (nudges a crumb toward you like a 'trade offer') Squeeet… prrrt. (waits for payment in the form of approval)", "🐭"),
    ("Pip… pip… wheeeep. (places one paw on its chest like making a solemn vow) Eep-eep—chik! (immediately breaks vow to investigate a speck of dust)", "🐭"),
    ("Chrrrk—squee-rrr, prrt! (rubs face with both paws like 'wipe the slate clean') Wheek… pip pip. (leans in, nose twitching like a detective)", "🐭"),
    ("Skrik-skrik, eep—eep—EEP. (panicked sprint of two steps) Prrr… wheep. (returns with composure, as if nothing happened)", "🐭"),
    ("Wheeeek, chik-chik-chrrt. (sits tall, chest puffed, delivering 'important' news) Squee… snorf. (adds a quiet foot shuffle for emphasis)", "🐭"),
    ("Bip! prrip—prrip, chrrt. (pushes an invisible button in the air) Eep… wheek. (waits for the 'result screen' to load)", "🐭"),
    ("Squeeet-squeeet—skrrt. (tries to whisper, but is biologically incapable) Chik… prrrt. (covers mouth with paw like it's being discreet)", "🐭"),
    ("Chrrt! pip pip pip—wheep. (rapid-fire 'bullet points,' clearly overprepared) Skrrk… eep. (stops to stare at a corner like it's heckling)", "🐭"),
    ("Wheek-wheek, prrrr—snorf. (slowly scoots a seed into a neat line like 'organizing variables') Chik! (nods once, satisfied with the methodology)", "🐭"),
    ("Eep-eep—bip, skrrt. (does a tiny hop like celebrating a 'small win') Squee… chrrrk. (immediately returns to serious face-rub mode)", "🐭"),
    ("Skrrk-skrrk, wheeeep. (presses forehead to the floor like thinking extremely hard) Pip… pip. (then looks up as if it solved physics)", "🐭"),
    ("Chik-chik, prrt-prrt—squee. (scratches behind ear as if recalling a complex theory) Wheep… eep. (shuffles closer to make sure you're listening)", "🐭"),
    ("Squee-rrip, chrrt-chrrt. (drags a napkin scrap like it's a blueprint) Wheek! (points nose at the scrap, proud of the 'diagram')", "🐭"),
    ("Bip-bip—snorf—pip. (sniffs your hand, then sniffs its own paws, comparing notes) Skrrt… chrrrk. (gives a small approving head-bob)", "🐭"),
    ("Wheeeep, eep-eep—chik. (leans back like 'consider the evidence') Prrt… squeeet. (leans forward like 'now consider my feelings')", "🐭"),
    ("Chrrt! skrrt-skrrt. (does a cautious sidestep like avoiding a 'calorie trap') Pip pip. (stares at you as if you set the trap)", "🐭"),
    ("Squee… wheep… CHIK! (builds suspense, then blurts the 'conclusion') Eep. (holds eye contact, daring you to disagree)", "🐭"),
    ("Skrrk—pip pip—prrt. (taps bowl rim like a judge's gavel) Wheek-wheek… (pauses as if waiting for silence in court) chrrt. (verdict delivered)", "🐭"),
    ("Eep-eep, snorf-snorf. (sniffs the air, then sniffs the floor, then looks offended) Squeeet—bip. (waves a paw like 'don't make me repeat myself')", "🐭"),
    ("Chik-chik—wheep. (leans in close, conspiratorial) Prrr… pip pip. (backs away slowly as if the secret is contagious)", "🐭"),
    ("Wheek! skrit-skrit. (tiny sprint to demonstrate 'urgency') Squee… chrrt. (returns to 'calm voice,' still vibrating)", "🐭"),
    ("Bip, prrip-prrip—eep. (counts with toe taps like doing math) Skrrk… wheeeep. (pretends the answer is obvious)", "🐭"),
    ("Squeeet-squeeet, chrrrk. (places one crumb on another crumb like 'stacking habits') Prrt. (gives a solemn nod to the crumb tower)", "🐭"),
    ("Chrrt-chrrt, wheep-wheep. (paws at the air like shaping clay—'molding routine') Eep! (startles itself mid-sculpture)", "🐭"),
    ("Skrrk, pip pip pip. (makes a straight line with tail like drawing a boundary) Wheek… (guards the boundary with intense seriousness)", "🐭"),
    ("Eep… squee… prrrt. (slowly rotates in place like reconsidering life choices) Chik! (stops abruptly as if arriving at wisdom)", "🐭"),
    ("Wheeeep, chrrt. (leans against a wall like a tired philosopher) Bip-bip. (perks up instantly at imaginary snack noises)", "🐭"),
    ("Pip pip—skrrt. (scoots backward as if demonstrating 'distance from temptation') Squee… wheep. (then leans forward again, suspicious of its own plan)", "🐭"),
    ("Chrrrk! eep-eep. (two quick squeaks like 'yes and yes') Prrr… (stares at you like 'write that down')", "🐭"),
    ("Skrit-skrit—wheek. (runs a tiny figure-eight like 'balanced approach') Chrrt. (stops at center like 'balance achieved')", "🐭"),
    ("Squee-rrr, prrt-prrt. (grooms fur vigorously like 'reset') Eep. (finishes with one dramatic whisker flick)", "🐭"),
    ("Wheep-wheep, pip. (raises one paw like asking permission) Chrrt! (answers itself immediately and proceeds anyway)", "🐭"),
    ("Bip-bip, snorf… (sniffs you, then sniffs the air above you like checking your 'aura') Squeeet. (backs away, apparently unimpressed)", "🐭"),
    ("Chrrt-chrrt—skrrk. (scratches the floor like underlining a sentence) Wheek… pip. (looks up like 'did you get that?')", "🐭"),
    ("Eep-eep, prrrt. (tucks paws in like composing a formal email) Squee… chrrrk. (then sends it telepathically to absolutely no one)", "🐭"),
    ("Skrrk—wheeeep. (leans into the wind that isn't there, heroic) Bip. (tiny nod: mission accepted)", "🐭"),
    ("Squeeet-squeeet, pip pip. (offers you a seed like a peace treaty) Chrrt. (takes it back immediately—negotiations continue)", "🐭"),
    ("Wheek, chrrt-chrrt. (places paws neatly like a polite meeting) Eep. (slides a crumb toward you like 'agenda item 1')", "🐭"),
    ("Prrt-prrt, skrit. (does a small 'drumroll' with toes) Squee… (reveals nothing, just enjoys suspense)", "🐭"),
    ("Chik-chik—snorf. (leans in to sniff your sleeve like confirming your credentials) Wheep. (approves, surprisingly)", "🐭"),
    ("Eep-EEP, skrrt. (tiny jump scare performance) Prrr… chrrt. (then acts like you overreacted)", "🐭"),
    ("Skrrk, pip… pip… (slow, deliberate squeaks like 'step-by-step') Wheeeep. (finishes with a confident tail sweep, as if concluding a seminar)", "🐭"),
    ("Squee-rrip, chrrt. (stares at the ceiling like consulting the gods) Bip. (receives divine guidance: none)", "🐭"),
    ("Wheep-wheep, prrrt. (circles your foot like marking territory) Eep. (then looks offended that you exist inside it)", "🐭"),
    ("Chrrt-chrrt—pip. (gently pushes your invisible 'portion' away) Squeeet. (then steals an invisible 'extra,' hypocritically)", "🐭"),
    ("Skrit-skrit, wheek. (pretends to write with tail tip) Prrr. (reads the 'notes' aloud to itself, proudly)", "🐭"),
    ("Eep-eep, chik. (two squeaks like quotation marks) Squee… chrrrk. (adds a foot-tap like a citation)", "🐭"),
    ("Bip-bip—skrrk. (leans in, nose twitching like a lie detector) Wheeeep. (backs away as if the truth was too spicy)", "🐭"),
    ("Chik, prrt-prrt. (wipes paws on face like erasing a mistake) Squee. (tries again with renewed seriousness)", "🐭"),
    ("Wheek-wheek, pip pip. (stares at a crumb like it owes rent) Chrrt. (then gently escorts it away, ceremonially)", "🐭"),
    ("Skrrk—eep. (one sharp squeak like a warning siren) Prrr… (soft follow-up squeak like 'but lovingly')", "🐭"),
    ("Squeeet, chrrt-chrrt. (leans forward like offering heartfelt advice) Wheep. (immediately gets distracted by its own tail)", "🐭"),
    ("Eep-eep—wheek. (hops twice as if saying 'repeat after me') Pip. (waits for your repetition; receives silence)", "🐭"),
    ("Chrrt, skrit-skrit. (scratches a tiny 'X' on the floor like marking a spot) Squee… (sits on the X like 'this is the plan')", "🐭"),
    ("Wheeeep, prrt. (exhales dramatically like finishing a workout) Bip-bip. (celebrates by inspecting imaginary cheese)", "🐭"),
    ("Skrrk-skrrk, pip pip. (rapid squeaks like a fast-speaking lawyer) Chik. (stops to groom—'objection sustained')", "🐭"),
    ("Squee-rrr, wheep. (leans into your gaze like a motivational coach) Eep. (then quietly hides behind the bowl, shy about inspiration)", "🐭"),
    ("Chik-chik, snorf-snorf. (does a careful perimeter check like 'environment audit') Wheek. (nods once: hazards detected)", "🐭"),
    ("Bip… pip… (slow squeaks like deep breathing) Prrr. (shoulders—tiny shoulders—relax noticeably)", "🐭"),
    ("Eep-EEP—chrrt. (one squeak too loud, then apologizes with a paw wave) Squee. (resumes at 'indoor voice')", "🐭"),
    ("Skrit, skrrt. (slides sideways like avoiding a 'trap tile') Wheep. (glances back to see if you noticed the technique)", "🐭"),
    ("Squeeet-squeeet, prrt-prrt. (taps bowl twice, then points at you—clearly your turn now) Chrrt. (waits, patient but intense)", "🐭"),
    ("Wheek, pip pip. (sets a crumb down gently like it's fragile) Eep. (backs away like 'respect the system')", "🐭"),
    ("Chrrt-chrrt—skrrk. (tilts head left, then right, then left again like comparing options) Squee. (chooses neither; chooses panic)", "🐭"),
    ("Bip-bip, wheeeep. (puffs cheeks like inflating courage) Prrt. (deflates immediately, but continues anyway)", "🐭"),
    ("Skrrk—pip. (one squeak like a 'reminder alarm') Wheep. (then sits quietly like a snooze button)", "🐭"),
    ("Squee… chrrrk. (carefully arranges bedding like 'meal prep') Eep. (then collapses into it like a champion)", "🐭"),
    ("Chik-chik, prrrt. (shuffles forward with slow confidence like 'sustainable pace') Wheek. (pauses to ensure you're still following)", "🐭"),
    ("Eep-eep, pip pip. (two squeaks like 'if-then') Chrrt. (adds a third squeak like 'unless')", "🐭"),
    ("Skrit-skrit—bip. (tries to hand you a crumb, misses, acts like it was intentional) Squeeet. (gives a tiny nod: 'gift delivered')", "🐭"),
    ("Wheeeep, snorf. (sniffs the air like scanning for snacks) Chrrt. (decides the air is 'unsafe,' retreats)", "🐭"),
    ("Squee-rrip, prrrr. (slow purring squeak like satisfaction) Eep. (eyes half-close as if finishing a heartfelt TED talk)", "🐭"),
    ("Bip-bip—chrrt. (plants feet wide like taking a 'stance') Wheek. (nods as if committing to an oath)", "🐭"),
    ("Skrrk, wheep-wheep. (leans close, whisper-squeaks like sharing gossip) Pip. (then looks around to see if anyone overheard)", "🐭"),
    ("Chrrt-chrrt, eep. (two squeaks like 'check, check') Squee. (one squeak like 'done')", "🐭"),
    ("Wheek-wheek—skrit. (paces three steps like counting) Prrt. (stops exactly on four like it planned it all along)", "🐭"),
    ("Squeeet, chik. (makes a tiny bow like thanking an audience) Eep. (immediately demands applause with expectant stare)", "🐭"),
    ("Eep-eep, prrrt-prrt. (does a gentle toe-drumming rhythm like 'keep it steady') Chrrt. (ends with a tidy whisker sweep, very orderly)", "🐭"),
    ("Skrrk—snorf—pip. (sniffs your palm, then nods like 'approved source') Wheep. (walks away as if paperwork is complete)", "🐭"),
    ("Chik-chik, wheeeep. (tries to climb something, fails, pretends it was a stretch) Squee. (looks at you like you're the unreliable one)", "🐭"),
    ("Bip, pip pip. (soft squeaks like reassurance) Prrr. (rests head briefly on its paws like 'it's okay, continue tomorrow')", "🐭"),
    ("Wheek! chrrt. (one loud squeak like 'start now') Eep. (then immediately takes a break, embodying contradiction)", "🐭"),
    ("Squee… wheep. (slow, gentle squeaks like a lullaby) Chrrt. (yawns so hard it becomes a statement)", "🐭"),
    ("Skrrk-skrrk, EEP! (spots a shadow, declares an emergency) Prrt. (realizes it was its own whisker, recovers dignity)", "🐭"),
    ("Chrrt-chrrt, pip. (sits still like listening carefully) Wheeeep. (nods once, as if granting permission to proceed)", "🐭"),
    ("Bip-bip—snorf. (sniffs the bowl rim like checking inventory) Squeeet. (shakes head like 'supplies low,' very dramatic)", "🐭"),
    ("Eep-eep, chik. (two squeaks like 'good effort') Prrr. (grooms your imaginary badge of honor)", "🐭"),
    ("Wheek-wheek, prrrt. (leans forward, paws clasped like pleading for consistency) Chrrt. (then points at the floor like 'right here, right now')", "🐭"),
    ("Skrit-skrit, pip pip. (makes a tiny 'staircase' from crumbs) Eep. (climbs one step and celebrates like a marathon finisher)", "🐭"),
    ("Chrrt—wheep. (squeaks softly like 'reset') Squee. (squeaks firmly like 'continue')", "🐭"),
    ("Bip… prrrt. (stares at you for a full second like a meaningful pause) Wheek. (breaks the tension by grooming one ear, casually profound)", "🐭"),
    ("Squee-rrip, chrrt-chrrt. (walks away two steps, returns one step—clearly demonstrating 'progress isn't linear') Wheeeep. (final nod, as if the message was perfectly delivered and totally understandable)", "🐭"),
]

# =============================================================================
# REAL TIPS - When you have White Mouse Archimedes (the telepathic translator)
# Practical, science-based weight control advice organized by category
# =============================================================================

REAL_TIPS = [
    # A. The "physics + biology" basics (1-10)
    ("Aim for a small calorie deficit (roughly 10–20% below maintenance). Big deficits = big hunger + bigger rebound risk.", "🔬"),
    ("Lose weight like a grown-up: slowly. Faster loss usually costs more muscle and sanity.", "🔬"),
    ("Use weekly averages, not daily scale drama. Bodies fluctuate like stock markets—mostly water and glycogen.", "🔬"),
    ("Track one thing consistently (weight trend, steps, calories, protein). Chaos is not a metric.", "🔬"),
    ("Protein is your appetite's bouncer. Higher protein increases fullness and helps preserve lean mass in a deficit.", "🔬"),
    ("Fiber is protein's best friend. More fiber tends to reduce energy intake by increasing satiety.", "🔬"),
    ("Strength training is 'anti-regain insurance.' More muscle = better maintenance and less 'skinny-fat' outcome.", "🔬"),
    ("Don't diet without a plan for maintenance. Weight loss is the tutorial; maintenance is the actual game.", "🔬"),
    ("Hunger is information, not an emergency. Mild hunger is normal; gnawing, constant hunger means adjust.", "🔬"),
    ("Make it boringly repeatable. The best diet is the one you can do on a random Tuesday in November.", "🔬"),
    
    # B. Eating structure that reduces "oops calories" (11-20)
    ("Eat a protein-forward breakfast if mornings are your snack gateway.", "🍽️"),
    ("Pre-commit to meal times (even loosely). Grazing all day is stealth-calories with sneakers on.", "🍽️"),
    ("Use the '3-2-1 plate': 3 parts veggies, 2 parts protein, 1 part smart carbs or fats.", "🍽️"),
    ("Start meals with vegetables or soup—volume first, calories later.", "🍽️"),
    ("Keep high-calorie 'extras' pre-portioned (nuts, cheese, chocolate). The bag is not a serving size.", "🍽️"),
    ("Put a speed bump between you and snacks: plate it, sit down, no phone.", "🍽️"),
    ("Don't eat directly from packages. That's how 'a few' becomes 'a documentary series.'", "🍽️"),
    ("Build meals, don't 'assemble vibes.' Random bites add up fast; meals are easier to regulate.", "🍽️"),
    ("Plan 1–2 enjoyable treats per week intentionally. Forbidden foods become haunted foods.", "🍽️"),
    ("Use a consistent lunch you genuinely like. Decision fatigue is a buffet's best employee.", "🍽️"),
    
    # C. Protein done properly (21-30)
    ("Target ~25–40 g protein per meal (adjust by body size/activity).", "🥩"),
    ("Pick lean proteins often: skyr/Greek yogurt, fish, poultry, beans+low-fat dairy, tofu/tempeh.", "🥩"),
    ("Protein snacks beat 'crunch snacks': yogurt, cottage cheese, edamame, jerky, protein shake.", "🥩"),
    ("Add protein to carbs (e.g., oats + yogurt; pasta + tuna/beans).", "🥩"),
    ("If you're hungry soon after eating, increase protein first before blaming your willpower.", "🥩"),
    ("Use protein as the 'anchor' of every meal—choose it first, then add the rest.", "🥩"),
    ("Consider a protein shake if convenience is your enemy (especially post-workout).", "🥩"),
    ("Include plant proteins (beans, lentils, soy) for fiber + satiety.", "🥩"),
    ("Watch 'protein bars': many are candy bars with gym memberships.", "🥩"),
    ("Don't chase perfection: 'higher than before' protein already helps.", "🥩"),
    
    # D. Fiber, volume, and the art of being full (31-40)
    ("Aim for 25–40 g fiber/day (increase gradually, drink water).", "🥗"),
    ("Add one 'volume vegetable' daily: cucumber, tomatoes, leafy greens, zucchini, cabbage.", "🥗"),
    ("Eat fruit whole more often than as juice. Chewing matters; juice is fruit on fast-forward.", "🥗"),
    ("Use legumes 3–5 times/week (lentil soup, chickpea salad, bean chili).", "🥗"),
    ("Choose whole grains when possible (oats, rye, buckwheat, brown rice).", "🥗"),
    ("Popcorn can be a great snack if not drowned in butter.", "🥗"),
    ("Soup and stews are 'calorie dilution' hacks (more water + volume).", "🥗"),
    ("Add berries for high fiber per calorie and strong satisfaction.", "🥗"),
    ("Add chia/flax to yogurt/oats for fiber + texture.", "🥗"),
    ("Use 'big salad, real protein'—salad alone is just crunchy air.", "🥗"),
    
    # E. Carbs and fats: make them work for you (41-50)
    ("Carbs aren't evil; unplanned carbs are sneaky. Portion them intentionally.", "🍞"),
    ("Prefer 'slow' carbs (potatoes, oats, legumes, whole grains) over ultra-processed sweets.", "🍞"),
    ("Keep fats, but measure them. Oils and nuts are healthy and also calorie-dense.", "🍞"),
    ("Use a teaspoon/tablespoon for oils—free-pouring is a calorie trust fall.", "🍞"),
    ("Choose low-fat cooking methods: air-fry, bake, grill, steam.", "🍞"),
    ("Swap 'fat + sugar combos' (pastries, ice cream) for either-or more often.", "🍞"),
    ("Use avocado/nuts strategically, not as 'because wellness.'", "🍞"),
    ("Potatoes are surprisingly filling—just don't turn them into fries with a side of regret.", "🍞"),
    ("Don't drink your carbs often (soda, sweet coffee). Liquids don't satisfy like solids.", "🍞"),
    ("If dinner cravings hit, add carbs earlier (some people over-restrict → rebound at night).", "🍞"),
    
    # F. Ultra-processed foods: keep them on a leash (51-60)
    ("Default to mostly minimally processed foods (not perfect—mostly).", "🏪"),
    ("Read labels for calorie density: compare kcal per 100 g; choose lower-density frequently.", "🏪"),
    ("Beware 'healthy' snacks (granola, trail mix). They can be calorie grenades with chia sprinkles.", "🏪"),
    ("Keep trigger foods out of arm's reach (or out of the house). Environment beats motivation.", "🏪"),
    ("Buy single servings of snacks you can't trust. Yes, it costs more. So does new pants.", "🏪"),
    ("Use the 80/20 rule: 80% nourishing, 20% joy. Joy is not optional.", "🏪"),
    ("Don't shop hungry. Hungry-you is a terrible financial advisor.", "🏪"),
    ("Make the healthy choice the easy choice (washed fruit visible, chopped veg ready).", "🏪"),
    ("If you eat ultra-processed foods, plate them—don't 'keyboard snack.'", "🏪"),
    ("Choose one 'fun food' per occasion, not the tasting menu of doom.", "🏪"),
    
    # G. Portion control that doesn't feel like punishment (61-70)
    ("Use smaller plates/bowls (simple, surprisingly effective).", "🍽️"),
    ("Serve once, then put food away before eating. Seconds become a deliberate act.", "🍽️"),
    ("Half your plate vegetables at most meals. Not sexy, very effective.", "🍽️"),
    ("Pre-portion nuts and cheese—they're tiny, mighty, and easily overdone.", "🍽️"),
    ("Use the 'hand method' when you can't measure: palm protein, fist carbs, thumb fats.", "🍽️"),
    ("In restaurants, ask for a box early and move half your meal out of the danger zone.", "🍽️"),
    ("Choose 'one upgrade': fries → salad, soda → water, dessert → shared.", "🍽️"),
    ("Beware sauces and dressings—measure or use them on the side.", "🍽️"),
    ("Add protein/veg first, then carbs/fats; fullness makes portions behave.", "🍽️"),
    ("Stop at 'satisfied,' not 'stuffed.' Stuffed is just satisfied, plus gravity.", "🍽️"),
    
    # H. Eating behavior: the hidden lever (71-80)
    ("Slow down: aim for ~15–20 minutes per meal. Satiety signals aren't on 5G.", "🧠"),
    ("Chew more (yes, really). Less speed = less accidental overeating.", "🧠"),
    ("Eat without screens sometimes. Your brain can't register fullness while binge-watching.", "🧠"),
    ("Use a 'hunger scale' (1–10) and start eating around 3–4, stop around 6–7.", "🧠"),
    ("If cravings hit, delay 10 minutes and drink water/tea—often the intensity drops.", "🧠"),
    ("Have a 'default rescue snack' (protein + fruit) for emergency hunger.", "🧠"),
    ("Don't let yourself get ravenous. That's when you start negotiating with cookies.", "🧠"),
    ("Create a 'kitchen closed' routine (tea + brush teeth + lights down).", "🧠"),
    ("Keep cutlery down between bites occasionally. It's weird at first, effective forever.", "🧠"),
    ("Treat stress-eating like a problem to solve, not a moral failing. Build alternate stress tools.", "🧠"),
    
    # I. Movement: fat loss help + maintenance superpower (81-90)
    ("Walk more. Steps are the stealth MVP of calorie burn and appetite regulation.", "🏃"),
    ("Set a realistic step target and increase gradually (e.g., +1,000/day each week).", "🏃"),
    ("Do strength training 2–4×/week (full-body works great).", "🏃"),
    ("Progressive overload matters: add reps, sets, or weight over time.", "🏃"),
    ("Add 'movement snacks': 5–10 minutes after meals (walk, stairs). Helps glucose control too.", "🏃"),
    ("Do cardio you can repeat (cycling, incline walk, swimming). The best cardio is sustainable cardio.", "🏃"),
    ("Increase NEAT: stand while calls, park farther, take stairs—tiny choices compound.", "🏃"),
    ("Keep workouts short if needed (20–30 min). Consistency beats heroic collapses.", "🏃"),
    ("Don't 'eat back' all exercise calories—machines overestimate and hunger negotiates aggressively.", "🏃"),
    ("Train for performance goals, not punishment. Punishment doesn't scale well.", "🏃"),
    
    # J. Sleep, stress, and hormones (91-100)
    ("Protect 7–9 hours of sleep; short sleep increases hunger and reduces restraint.", "🌙"),
    ("Keep consistent sleep/wake times—your appetite likes schedules too.", "🌙"),
    ("Cut caffeine late (many people: after ~2 pm). Sleep debt makes cravings louder.", "🌙"),
    ("Create a wind-down ritual (dim lights, no doomscrolling).", "🌙"),
    ("Stress management is weight management: breathing, walks, journaling, therapy—pick your tool.", "🌙"),
    ("Don't diet harder when stressed; diet smarter (simpler meals, more protein, more routine).", "🌙"),
    ("Alcohol is appetite jet fuel and adds calories—reduce frequency or set a drink limit.", "🌙"),
    ("If you're stuck, take a 1–2 week maintenance break (same healthy habits, more calories). It can reduce burnout.", "🌙"),
    ("Design your environment: keep healthy foods visible, treats less accessible, routines automatic.", "🌙"),
    ("Have a relapse plan: 'When I overeat, I do the next meal normally.' No fasting, no punishment—just back to baseline.", "🌙"),
]

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_tip_count(has_translator: bool = False) -> int:
    """Get the total number of tips available.
    
    Args:
        has_translator: If True, user has White Mouse Archimedes and gets real tips.
                       If False, user gets rodent language tips.
    """
    return len(REAL_TIPS) if has_translator else len(RODENT_LANGUAGE_TIPS)


def get_tip_by_index(index: int, has_translator: bool = False) -> Tuple[str, str]:
    """
    Get a specific tip by index.
    
    Args:
        index: The tip index (will wrap around if > total tips)
        has_translator: If True, user has White Mouse Archimedes and gets real tips.
                       If False, user gets rodent language tips.
    
    Returns:
        tuple: (tip_text, category_emoji)
    """
    tips_list = REAL_TIPS if has_translator else RODENT_LANGUAGE_TIPS
    index = index % len(tips_list)
    return tips_list[index]


def has_telepathic_translator(adhd_data: dict) -> bool:
    """
    Check if the user has collected White Mouse Archimedes (scientist_009).
    
    This entity provides "telepathic translation" ability, allowing the user
    to understand the Rodent Squad's weight control wisdom instead of just
    hearing squeaks.
    
    Args:
        adhd_data: The adhd_buster data dict containing entitidex progress
        
    Returns:
        True if user has scientist_009 (normal or exceptional), False otherwise
    """
    try:
        from gamification import get_entitidex_manager
        manager = get_entitidex_manager(adhd_data)
        TRANSLATOR_ENTITY_ID = "scientist_009"  # White Mouse Archimedes
        
        # Check if collected (normal or exceptional)
        has_normal = TRANSLATOR_ENTITY_ID in manager.progress.collected_entity_ids
        has_exceptional = manager.progress.is_exceptional(TRANSLATOR_ENTITY_ID)
        
        return has_normal or has_exceptional
    except Exception:
        return False
