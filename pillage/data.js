/* Pillage the Reefer: the seas, ports, cargo and people.
   Original characters and writing. Ports are real old Caribbean harbors and the coastlines are real (coasts.js); the strains and people are made up. */
(function () {
  'use strict';

  var GOODS = {
    tangerine: {name: 'Tortuga Tangerine', icon: '🍊', base: 28, home: 'tortuga', note: 'Bright and citrusy. Smells like a sunny deck.'},
    purple:    {name: 'Port Royal Purple', icon: '🍇', base: 40, home: 'portroyal', note: 'Fancy. Pinky-out stuff.'},
    breath:    {name: "Buccaneer's Breath", icon: '💨', base: 32, home: 'petitgoave', note: 'Earthy and bold, like an old sea dog.'},
    haze:      {name: 'Havana Haze', icon: '🌫️', base: 44, home: 'havana', note: 'Smooth, slow and very sure of itself.'},
    nectar:    {name: 'Nassau Nectar', icon: '🍯', base: 36, home: 'nassau', note: 'Sweet as island honey.'},
    candy:     {name: 'Cartagena Candy', icon: '🍬', base: 48, home: 'cartagena', note: 'Sugary, sticky and a little bit showy.'},
    pineapple: {name: 'Portobelo Pineapple', icon: '🍍', base: 38, home: 'portobelo', note: 'Tropical. Wears a tiny hat.'},
    cloud:     {name: 'Curaçao Cloud', icon: '☁️', base: 52, home: 'willemstad', note: 'Light, fluffy and impossible to find in a hurry.'},
    vanilla:   {name: 'Veracruz Vanilla', icon: '🌼', base: 42, home: 'veracruz', note: 'Sweet, creamy and slow-cured, like a long siesta.'},
    fountain:  {name: 'Fountain of Youth', icon: '⛲', base: 46, home: 'staugustine', note: 'Makes you feel nineteen. Results not guaranteed.'},
    rumcake:   {name: 'Bajan Rum Cake', icon: '🍰', base: 40, home: 'barbados', note: 'Rich, boozy-sweet and gone too soon.'},
    kraken:    {name: 'Kraken Kush', icon: '🐙', base: 150, rare: 'Only found in the holds of merchant ships.', note: 'Legendary. Grips you with all eight arms.'},
    pearl:     {name: 'Black Pearl', icon: '⚫', base: 170, rare: 'Only carried by the strongest pirate ships.', note: 'Dark, glossy and very illegal. The Crown would love a word with whoever owns it.'},
    mermaid:   {name: "Mermaid's Kiss", icon: '🧜', base: 120, rare: 'Only found floating at sea.', note: 'Drifts in on the tide, sweet and salty.'},
    // Products: made in one port, wanted most in a few others (they pay a premium), and their prices swing by their own amount.
    hash:      {name: "Smuggler's Hash", icon: '🧱', base: 66, home: 'petitgoave', kind: 'product', swing: 0.3, wants: ['havana', 'cartagena', 'barbados'],
      note: 'Pressed bricks of resin. Strong, dense and easy to stack. Prized in Havana, Cartagena and Barbados.'},
    rosin:     {name: 'Amber Rosin', icon: '🔶', base: 84, home: 'willemstad', kind: 'product', swing: 0.5, wants: ['nassau', 'staugustine', 'veracruz'],
      note: 'Golden and glassy, squeezed by hand. Pricey, and its price jumps about from day to day. Prized in Nassau, St. Augustine and Veracruz.'},
    biscuits:  {name: "Cook's Biscuits", icon: '🍪', base: 34, home: 'nassau', kind: 'product', swing: 0.2, wants: ['tortuga', 'portobelo', 'barbados'],
      note: 'Baked by a very relaxed cook. Cheap and steady. Prized in Tortuga, Portobelo and Barbados.'},
    // Grown in your own beds at the hideout (see GENES below). Any market buys them; none sells them.
    g_home:  {name: 'Homegrown', icon: '🌿', base: 22, kind: 'grown', note: 'Leafy, seedy and honest. What comes up in your beds before you’ve bred anything worth naming.'},
    g_nl:    {name: 'Northern Lights', icon: '🌌', base: 64, kind: 'grown', note: 'Bred in your own beds from Afghani and Thai. Short, dense and famously sleepy.'},
    g_skunk: {name: 'Skunk #1', icon: '🦨', base: 66, kind: 'grown', note: 'Bred in your own beds from Afghani, Colombian Gold and Acapulco Gold. You can smell it from the next island.'},
    g_haze:  {name: 'Original Haze', icon: '🌁', base: 80, kind: 'grown', note: 'Bred in your own beds from four landraces. Tall, slow to finish and very, very up.'},
    g_ak47:  {name: 'AK-47', icon: '🎯', base: 84, kind: 'grown', note: 'Bred in your own beds from Colombian, Mexican, Thai and Afghani. Quick to finish for something so tall.'},
    g_shiva: {name: 'Shiva Skunk', icon: '🔱', base: 78, kind: 'grown', note: 'Bred in your own beds from Northern Lights and Skunk #1. Heavy, musky and calm.'},
    g_ssh:   {name: 'Super Silver Haze', icon: '🥈', base: 100, kind: 'grown', note: 'Bred in your own beds from Skunk, Northern Lights and Haze. Frosty, bright and in demand everywhere.'},
    g_jack:  {name: 'Jack Herer', icon: '📗', base: 112, kind: 'grown', note: 'Bred in your own beds from Haze, Northern Lights and Shiva Skunk. The prize of any breeder’s notebook.'},
    // Brick Weed: cheap pressed schwag, sold almost everywhere. Not worth much, but you can load it in a cannon.
    brick:     {name: 'Brick Weed', icon: '🟫', base: 12, home: 'nassau', kind: 'brick', swing: 0.2,
      note: 'Pressed brown brick, seeds, stems and all. Nobody smokes it on purpose, but it burns like a bonfire and fits a cannon nicely.'}
  };
  var COMMON = ['tangerine', 'purple', 'breath', 'haze', 'nectar', 'candy', 'pineapple', 'cloud', 'vanilla', 'fountain', 'rumcake'];

  /* The five seas. Their coastlines, crossings and sea lanes are real geography, generated into coasts.js and merged in below. */
  var MAPS = {
    windward: {name: 'The Windward Passage', short: 'Windward Passage', blurb: 'Between Cuba, Hispaniola and Jamaica. Home waters.'},
    straits: {name: 'The Florida Straits', short: 'Florida Straits', blurb: 'Havana, Nassau and a thousand little cays.'},
    main: {name: 'The Spanish Main', short: 'Spanish Main', blurb: 'Old treasure ports along the coast from Panama to Venezuela.'},
    gulf: {name: 'The Gulf of Mexico', short: 'Gulf of Mexico', blurb: 'Wide open water west of Cuba, with Veracruz at the far end.'},
    antilles: {name: 'The Lesser Antilles', short: 'Lesser Antilles', blurb: 'A long arc of green islands, and Barbados out on its own in the trade winds.'}
  };

  /* Ports. Where the ship ties up (dock, in the water) and where the houses are drawn (town, on land) come from coasts.js. */
  var PORTS = {
    tortuga:    {name: 'Tortuga', map: 'windward', sells: ['tangerine', 'breath', 'purple', 'brick'], yard: true, who: 'ruthie',
                 blurb: 'A rocky little island full of hammocks, gossip and suspicious-smelling smoke.'},
    portroyal:  {name: 'Port Royal', map: 'windward', sells: ['purple', 'tangerine', 'breath', 'brick'], yard: true, who: 'percival',
                 blurb: 'The richest, rowdiest harbor in the Caribbean. The wigs are very tall here.'},
    petitgoave: {name: 'Petit-Goâve', map: 'windward', sells: ['breath', 'tangerine', 'pineapple', 'hash'], yard: false, who: 'toussaint',
                 blurb: 'A quiet old buccaneer harbor where everyone is mending a net or pretending to.'},
    havana:     {name: 'Havana', map: 'straits', sells: ['haze', 'nectar', 'fountain', 'brick'], yard: true, who: 'catalina',
                 blurb: 'Grand walls, grand ships and the finest rollers on any sea.'},
    nassau:     {name: 'Nassau', map: 'straits', sells: ['nectar', 'haze', 'tangerine', 'biscuits', 'brick'], yard: false, who: 'mildew',
                 blurb: 'A pirate republic of palm trees, hammocks and very relaxed rules.'},
    cartagena:  {name: 'Cartagena', map: 'main', sells: ['candy', 'pineapple', 'cloud'], yard: true, who: 'quill',
                 blurb: 'A walled city of balconies, bells and one very busy botanist.'},
    portobelo:  {name: 'Portobelo', map: 'main', sells: ['pineapple', 'candy', 'breath', 'brick'], yard: false, who: 'prudence',
                 blurb: 'Sleepy treasure port. Somebody important is on holiday here.'},
    willemstad: {name: 'Willemstad', map: 'main', sells: ['cloud', 'candy', 'nectar', 'rosin'], yard: true, who: 'ines',
                 blurb: 'Colorful houses, a floating bridge and a famous captain in retirement.'},
    staugustine: {name: 'St. Augustine', map: 'straits', sells: ['fountain', 'nectar', 'tangerine'], yard: false, who: 'bartholomew',
                 blurb: 'The oldest town in Florida. Some of the residents feel it.'},
    veracruz:   {name: 'Veracruz', map: 'gulf', sells: ['vanilla', 'haze', 'fountain', 'brick'], yard: true, who: 'esperanza',
                 blurb: 'A busy old harbor that smells of vanilla, tar and very long lunches.'},
    barbados:   {name: 'Barbados', map: 'antilles', sells: ['rumcake', 'cloud', 'pineapple', 'brick'], yard: true, who: 'clementine',
                 blurb: 'Bridgetown, on Carlisle Bay. Flying fish, cricket and a rum shop that never seems to close.'}
  };

  /* Buried treasure. A rumor marks the spot on your chart; the Emerald Bale needs all three map pieces. */
  var STASHES = {
    s1: {name: 'Navassa', map: 'windward', piece: true, gold: 150, loot: {mermaid: 3},
         text: 'You dig past three goats and one very offended crab. Clunk! A chest! Inside: the first piece of Captain Featherstone’s map, 150 doubloons and 3 bales of Mermaid’s Kiss.'},
    s2: {name: 'the Dry Tortugas', map: 'straits', piece: true, gold: 250, loot: {kraken: 1},
         text: 'Under a palm tree shaped like a question mark you find the second piece of the map, 250 doubloons and a bale of Kraken Kush.'},
    s3: {name: 'Providencia', map: 'main', piece: true, gold: 300, loot: {kraken: 2},
         text: 'Behind a rock that looks like a sleeping landlord: the third piece of the map, 300 doubloons and 2 bales of Kraken Kush.'},
    alacranes: {name: 'the Alacranes Reef', map: 'gulf', gold: 300, loot: {mermaid: 2},
         text: 'A very rude seagull watches you dig. Clunk! A little chest: 300 doubloons and 2 bales of Mermaid’s Kiss. The seagull takes one biscuit as tax.'},
    tobagocays: {name: 'the Tobago Cays', map: 'antilles', gold: 350, loot: {kraken: 1},
         text: 'Between two turtles and a very confused pelican you find a chest: 350 doubloons and a bale of Kraken Kush.'},
    emerald: {name: 'Serrana Bank', map: 'main', needs: 3, gold: 2000, loot: {},
         text: 'The haze parts. You dig, and dig, and… there it is: the Emerald Bale, wrapped in old sailcloth and smelling like every good day you ever had. Under it, 2,000 doubloons and a note in Ines’s hand: “Share some.”'}
  };

  /* People. Each node: text, then options. Options may need a condition (if) and may do something (do). */
  var PEOPLE = {
    ruthie: {
      name: 'Mama Ruthie Barnacle', role: 'Keeper of the Leaky Lantern tavern', icon: '🍺', port: 'tortuga',
      start: {text: 'Well, well. A fresh captain with an empty hold and a parrot full of opinions. Welcome to Tortuga, love. What’ll it be?', options: [
        {label: 'How does a pirate make a living around here?', next: 'trade'},
        {label: 'Heard any good rumors?', next: 'rumor', if: '!hint:s1'},
        {label: 'Tell me that rumor again.', next: 'rumor2', if: 'hint:s1'},
        {label: 'Where can a ship go from here?', next: 'where'},
        {label: 'Know any good jokes?', next: 'joke'},
        {label: 'Just passing through.', end: true}]},
      joke: {text: 'A captain told me this one last week. Why does corn always cost a dollar? Because it’s a buck-an-ear! …Buccaneer, love. Say it fast. The real word comes from boucan, the wooden frame the old hunters on Hispaniola smoked their meat on. The French borrowed it from the Tupi people of Brazil.', options: [{label: 'Good one, Ruthie.', next: 'start'}]},
      trade: {text: 'Buy it cheap where it grows, sell it dear where it doesn’t. Tortuga Tangerine grows like a weed here, mostly because it is one. Haul it somewhere fancy, like Havana or the Spanish Main, and watch the coin roll in.', options: [{label: 'Buy low, sell high. Got it.', next: 'start'}]},
      rumor: {text: 'Old Captain Ines Featherstone grew the finest crop that ever sailed: the Emerald Bale. Before she retired she buried it and tore her map in three. One piece is on Navassa, a lonely rock south-west of here. Only goats live there. Very judgmental goats.', do: 'hint:s1', options: [{label: 'I’ll go have a look.', next: 'start'}]},
      rumor2: {text: 'Navassa, love. South-west, between here and Jamaica. Follow the smell of goat.', options: [{label: 'Thanks, Ruthie.', next: 'start'}]},
      where: {text: 'Sail west past the tip of Cuba for the Florida Straits: Havana and Nassau. Sail off the bottom of the chart for the Spanish Main: Cartagena and friends. Sail east past Hispaniola for the Lesser Antilles and Barbados. Mind the customs cutters, with their blue sails, and the pirates with black ones. Every cutter flies its own king’s flag: British red, Spanish white with a red X, French white, Dutch stripes. None of them has a sense of humor.', do: 'know:havana,know:cartagena,know:barbados', options: [{label: 'Blue sails, black sails. Noted.', next: 'start'}]}
    },
    percival: {
      name: 'Lord Percival Fopsworth III', role: 'Gentleman of delicate constitution', icon: '🎩', port: 'portroyal',
      start: {text: 'Ah! A sea captain. Do not be alarmed by my wig; it is perfectly normal for it to be this tall. I require… medicine. For my gout. It is extremely medicinal.', options: [
        {label: 'What kind of medicine?', next: 'ask', if: '!quest:percival'},
        {label: 'Here’s your Havana Haze.', next: 'done', if: 'can:percival'},
        {label: 'How is the gout?', next: 'after', if: 'done:percival'},
        {label: 'Any news in Port Royal?', next: 'news'},
        {label: 'Good day, my lord.', end: true}]},
      ask: {text: 'Havana Haze. Five bales. My physician insists, and my physician is also me. Bring them and I shall pay three hundred doubloons, which I am told is a lot of money.', options: [
        {label: 'Deal.', do: 'quest:percival', next: 'start'}, {label: 'Maybe later.', next: 'start'}]},
      done: {text: 'Splendid! My gout already feels… wiggly. Three hundred doubloons, as promised. Tell no one. Especially my mother.', do: 'complete:percival', options: [{label: 'My lips are sealed.', next: 'start'}]},
      after: {text: 'Never better. I have taken up interpretive dance. The servants are concerned.', options: [{label: 'Glad to hear it.', next: 'start'}]},
      news: {text: 'They say the Customs Commodore takes her holidays in Portobelo. Even the law needs a nap, apparently.', do: 'know:portobelo', options: [{label: 'Interesting.', next: 'start'}]}
    },
    toussaint: {
      name: 'Grandpère Toussaint', role: 'Retired buccaneer, part-time net mender', icon: '🎣', port: 'petitgoave',
      start: {text: 'Sit, sit. Forty years I sailed these waters. Now I mend nets and tell stories. Mostly the stories. The nets are a mess.', options: [
        {label: 'Tell me about pillaging.', next: 'pillage'},
        {label: 'Do you need anything?', next: 'ask', if: '!quest:toussaint'},
        {label: 'Two bales of Mermaid’s Kiss, as promised.', next: 'done', if: 'can:toussaint'},
        {label: 'Know a safe place to stash cargo?', next: 'cave', if: '!base'},
        {label: 'Any advice for a smuggler?', next: 'smuggle'},
        {label: 'Farewell, Grandpère.', end: true}]},
      cave: {text: 'Île-à-Vache, the little cow island just south of here. The old buccaneer crews met there. There’s a dry cave above the beach with a door that still locks, and it’s mine. Five hundred doubloons and the key is yours. Whatever you leave in there stays there, even if the sea takes you.', do: 'base:know', options: [
        {label: 'Here’s five hundred doubloons.', do: 'base:buy', if: 'gold:500', next: 'key'},
        {label: 'I can’t afford it yet.', if: '!gold:500', next: 'start'},
        {label: 'Maybe later.', if: 'gold:500', next: 'start'}]},
      key: {text: 'The key is heavy, rusty and smells of goat. Sail into the cove on the south side of Île-à-Vache and she’s all yours. Leave your spare gold there. The sea is greedy.', options: [{label: 'Thank you, Grandpère.', next: 'start'}]},
      smuggle: {text: 'Customs sniff for cargo in the open hold. A good shipwright can build you a smuggler’s hold behind a false bulkhead, and whatever rides in there, they never find. Keep your Kraken Kush and Black Pearl in it. Those, they take on sight.', options: [{label: 'False bulkhead. Got it.', next: 'start'}]},
      pillage: {text: 'Fat merchant ships waddle across the sea like ducks full of bread. Sail right into one and you can try boarding her. More cannons, better odds. Cannons are what pirates have instead of manners.', options: [{label: 'Ducks full of bread. Got it.', next: 'start'}]},
      ask: {text: 'Mermaid’s Kiss. The bales that float in on the tide, sweet as island honey. Keep your eyes on the water. Bring me two and I’ll pay three hundred fifty doubloons and tell you a story.', options: [
        {label: 'You’ve got a deal.', do: 'quest:toussaint', next: 'start'}, {label: 'Not today.', next: 'start'}]},
      done: {text: 'Ahh. Smells like the good old days. Here is your gold. And the story: never trust a goat. That is the whole story.', do: 'complete:toussaint', options: [{label: 'Words to live by.', next: 'start'}]}
    },
    catalina: {
      name: 'Doña Catalina Humo', role: 'Master roller of Havana', icon: '🍃', port: 'havana',
      start: {text: 'Everyone thinks they can roll. Everyone is wrong. Welcome to Havana, Captain. Do not touch anything on my table.', options: [
        {label: 'Can you teach me to roll?', next: 'teach'},
        {label: 'Need anything shipped?', next: 'ask', if: '!quest:catalina'},
        {label: 'Ten bales of Tortuga Tangerine, Doña.', next: 'done', if: 'can:catalina'},
        {label: 'Adiós.', end: true}]},
      teach: {text: 'No. But I will tell you this for free: Havana pays well for Port Royal Purple, and the Customs cutters here are thick as mosquitoes. Pay them, outrun them or outsmart them. Never cry in front of them. Oh, and Nassau buys anything. Anything. And west of here, past the edge of the chart, Veracruz grows a vanilla people write poems about.', do: 'know:nassau,know:veracruz', options: [{label: 'No crying. Understood.', next: 'start'}]},
      ask: {text: 'Ten bales of Tortuga Tangerine. I am experimenting with citrus notes. Four hundred doubloons.', options: [
        {label: 'Consider it done.', do: 'quest:catalina', next: 'start'}, {label: 'Another time.', next: 'start'}]},
      done: {text: 'Perfect. Bright as a sunrise. Four hundred doubloons, and you may now touch exactly one thing on my table. Not that one.', do: 'complete:catalina', options: [{label: 'Gracias.', next: 'start'}]}
    },
    mildew: {
      name: 'Captain Mildred “Mildew” Mudge', role: 'Retired pirate, professional hammock tester', icon: '🏝️', port: 'nassau',
      start: {text: 'Shh. I’m resting. I’ve been resting for about thirty years. Big job, resting.', options: [
        {label: 'Any treasure around here?', next: 'treasure', if: '!hint:s2'},
        {label: 'Where was that treasure again?', next: 'again', if: 'hint:s2'},
        {label: 'Why do they call you Mildew?', next: 'nickname'},
        {label: 'Anything up the Florida coast?', next: 'florida'},
        {label: 'Sweet dreams.', end: true}]},
      florida: {text: 'St. Augustine, up the coast to the north-west. Fella there says he’s three hundred years old. Never once seen him in a hammock, so I don’t trust him.', do: 'know:staugustine', options: [{label: 'Noted.', next: 'start'}]},
      treasure: {text: 'Mmh. Ines Featherstone hid a piece of her map on the Dry Tortugas, way out west past the Florida Keys. I’d fetch it myself, but this hammock isn’t going to lie in itself.', do: 'hint:s2', options: [{label: 'Thanks, Mildew.', next: 'start'}]},
      again: {text: 'Dry Tortugas. West. Past the Keys. Shh.', options: [{label: 'Shh. Right.', next: 'start'}]},
      nickname: {text: 'I have been in this hammock a long time, Captain. A long, long time.', options: [{label: 'Fair enough.', next: 'start'}]}
    },
    quill: {
      name: 'Professor Ignatius Quill', role: 'Botanist, author, enthusiast', icon: '📚', port: 'cartagena',
      start: {text: 'Fascinating! A specimen! I mean, a visitor. I’m cataloguing every strain in the Caribbean for my book, Leaves of Considerable Interest.', options: [
        {label: 'Tell me about your book.', next: 'book'},
        {label: 'Seen any old maps?', next: 'maps', if: '!hint:s3'},
        {label: 'Where was that map piece again?', next: 'again', if: 'hint:s3'},
        {label: 'Who else should I meet?', next: 'who'},
        {label: 'Need a specimen?', next: 'ask', if: '!quest:quill'},
        {label: 'One bale of Kraken Kush, Professor.', next: 'done', if: 'can:quill'},
        {label: 'Good luck with the book.', end: true}]},
      who: {text: 'Captain Ines Featherstone herself! She retired to Willemstad on Curaçao, east along the coast. She grows Curaçao Cloud now and refuses to talk about treasure. Mostly.', do: 'know:willemstad', options: [{label: 'Willemstad. Thanks.', next: 'start'}]},
      book: {text: 'Volume one is two thousand pages. Volume two is mostly sketches of leaves. Volume three is a cry for help.', options: [{label: 'I’ll wait for the movie.', next: 'start'}]},
      maps: {text: 'Indeed! I found Captain Featherstone’s notes in the city archive. Her third map piece is on Providencia, the little island far to the north-west. Pirates loved it. Lots of hiding places and very few landlords.', do: 'hint:s3', options: [{label: 'Providencia. Thank you!', next: 'start'}]},
      again: {text: 'Providencia! North-west! Do take notes, Captain.', options: [{label: 'Noted.', next: 'start'}]},
      ask: {text: 'The legendary Kraken Kush! Only ever found in the holds of merchant ships. Bring me one bale and I’ll pay six hundred doubloons. For science.', options: [
        {label: 'For science!', do: 'quest:quill', next: 'start'}, {label: 'Science can wait.', next: 'start'}]},
      done: {text: 'Magnificent! Tentacular! Six hundred doubloons, and a footnote in volume four.', do: 'complete:quill', options: [{label: 'A footnote! I’m honored.', next: 'start'}]}
    },
    prudence: {
      name: 'Commodore Prudence Pinchwhistle', role: 'Crown Customs, on holiday', icon: '👒', port: 'portobelo',
      start: {text: 'I am on holiday, Captain. So I did not see your cargo, and you did not see me in this straw hat. Agreed?', options: [
        {label: 'Agreed.', next: 'tip'},
        {label: 'Do you need anything?', next: 'ask', if: '!quest:prudence'},
        {label: 'Eight bales of Curaçao Cloud, Commodore.', next: 'done', if: 'can:prudence'},
        {label: 'Enjoy your holiday.', end: true}]},
      tip: {text: 'Good. A little tip, between friends I am pretending not to have: my officers can be bribed, outrun or confused. Polite captains confuse them more often.', options: [{label: 'Very helpful.', next: 'start'}]},
      ask: {text: 'Eight bales of Curaçao Cloud. It is for… evidence. Very important evidence, which I will be evaluating on this beach. Five hundred doubloons.', options: [
        {label: 'Happy to help the law.', do: 'quest:prudence', next: 'start'}, {label: 'Maybe later.', next: 'start'}]},
      done: {text: 'This evidence is extremely thorough. Five hundred doubloons, and I will tell my cutters you are a vicar. They will be much less nosy.', do: 'complete:prudence', options: [{label: 'Bless you, Commodore.', next: 'start'}]}
    },
    ines: {
      name: 'Captain Ines Featherstone', role: 'Legendary grower, happily retired', icon: '🦜', port: 'willemstad',
      start: {text: 'So you’re the one sailing about digging up my old map. Good. I’m too old to dig. My knees retired before I did.', options: [
        {label: 'Why did you tear up the map?', next: 'why'},
        {label: 'Where are the pieces?', next: 'pieces', if: '!pieces:3'},
        {label: 'I have all three pieces!', next: 'three', if: 'pieces:3', also: '!found:emerald'},
        {label: 'I found the Emerald Bale!', next: 'won', if: 'found:emerald'},
        {label: 'Farewell, Captain.', end: true}]},
      why: {text: 'To see if anyone was worth it. Also, I was very relaxed that evening and it seemed like a wonderful idea.', options: [{label: 'Fair.', next: 'start'}]},
      pieces: {text: 'One on Navassa, one on the Dry Tortugas, one on Providencia. Bring them together and look for the cay that’s always wrapped in smoke.', do: 'hint:s1,hint:s2,hint:s3', options: [{label: 'Thank you, Captain.', next: 'start'}]},
      three: {text: 'All three! Then you know where to go: Serrana Bank, a few lonely cays out in the open sea north of the Main. Follow the haze. The Emerald Bale is yours if you can dig it up.', options: [{label: 'I’m on my way.', next: 'start'}]},
      won: {text: 'Ha! Then you’re a Legend of the Reefer now. Try not to let it go to your head. It went to mine for about forty years.', options: [{label: 'I’ll try.', next: 'start'}]}
    },
    bartholomew: {
      name: 'Brother Bartholomew Spry', role: 'Says he is 312 years old', icon: '⛲', port: 'staugustine',
      start: {text: 'Welcome to St. Augustine, the oldest town in Florida! I’m Brother Bartholomew, and I’m three hundred and twelve years old. I drank from the fountain. Don’t tell anyone. Tell everyone.', options: [
        {label: 'Three hundred and twelve? Really?', next: 'age'},
        {label: 'Do you need anything?', next: 'ask', if: '!quest:bartholomew'},
        {label: 'Five bales of Veracruz Vanilla, Brother.', next: 'done', if: 'can:bartholomew'},
        {label: 'Where else should I sail?', next: 'where'},
        {label: 'Farewell, Brother.', end: true}]},
      age: {text: 'Give or take a century. The secret is the Fountain of Youth, a good nap and never, ever arguing with a pelican.', options: [{label: 'Words to live by.', next: 'start'}]},
      ask: {text: 'I’m turning three hundred and thirteen! I need a cake, and a cake needs vanilla. Five bales of Veracruz Vanilla, from the Gulf of Mexico. Three hundred fifty doubloons.', options: [
        {label: 'Happy early birthday. Deal.', do: 'quest:bartholomew', next: 'start'}, {label: 'Maybe later.', next: 'start'}]},
      done: {text: 'Vanilla! It smells exactly like my two hundredth birthday. Three hundred fifty doubloons, and a candle for your trouble. Just the one. We’d need a bigger cake.', do: 'complete:bartholomew', options: [{label: 'Many happy returns.', next: 'start'}]},
      where: {text: 'West, past Havana and off the edge of the chart, lies the Gulf of Mexico. Veracruz is at the far end. Lovely people. Very long lunches.', do: 'know:veracruz', options: [{label: 'Thanks, Brother.', next: 'start'}]}
    },
    esperanza: {
      name: 'Doña Esperanza Vainilla', role: 'Vanilla grower and dessert critic', icon: '🌼', port: 'veracruz',
      start: {text: 'Smell that, Captain? Vanilla. Veracruz grows the best in the world, and I will fight anyone who says otherwise. Politely.', options: [
        {label: 'What makes it so special?', next: 'vanilla'},
        {label: 'Do you need anything?', next: 'ask', if: '!quest:esperanza'},
        {label: 'Four bales of Bajan Rum Cake, Doña.', next: 'done', if: 'can:esperanza'},
        {label: 'Heard any rumors?', next: 'rumor', if: '!hint:alacranes'},
        {label: 'Where was that reef again?', next: 'again', if: 'hint:alacranes'},
        {label: 'Adiós, Doña.', end: true}]},
      vanilla: {text: 'Patience. Every pod is cured in the sun for months. It is the slowest crop on earth, which is why everyone here takes very long lunches. Sell it far away. In Barbados they go wild for it.', do: 'know:barbados', options: [{label: 'Patience. Got it.', next: 'start'}]},
      ask: {text: 'I am inventing the perfect dessert, and it needs Bajan Rum Cake, all the way from Barbados. Four bales, and I pay four hundred fifty doubloons. You also get the first bite.', options: [
        {label: 'For dessert!', do: 'quest:esperanza', next: 'start'}, {label: 'Another time.', next: 'start'}]},
      done: {text: 'Rum, sugar, butter, more rum. Perfect. Four hundred fifty doubloons, and the first bite is yours. A small bite.', do: 'complete:esperanza', options: [{label: 'Delicious.', next: 'start'}]},
      rumor: {text: 'Fishermen say an old captain buried a chest on the Alacranes Reef, north of the Yucatán. They also say a very rude seagull lives there, so be quick.', do: 'hint:alacranes', options: [{label: 'I’ll bring biscuits.', next: 'start'}]},
      again: {text: 'The Alacranes Reef, north of the Yucatán. Mind the seagull.', options: [{label: 'Gracias.', next: 'start'}]}
    },
    clementine: {
      name: 'Auntie Clementine Flyingfish', role: 'Runs the rum shop on Carlisle Bay', icon: '🐟', port: 'barbados',
      start: {text: 'Come in out of the sun, Captain, you look peaky. Sit down, eat something, and then we can talk business.', options: [
        {label: 'What’s good in Barbados?', next: 'good'},
        {label: 'Do you need anything?', next: 'ask', if: '!quest:clementine'},
        {label: 'Four bales of Fountain of Youth, Auntie.', next: 'done', if: 'can:clementine'},
        {label: 'Any buried treasure around here?', next: 'treasure', if: '!hint:tobagocays'},
        {label: 'Where was that treasure again?', next: 'again', if: 'hint:tobagocays'},
        {label: 'Thank you, Auntie.', end: true}]},
      good: {text: 'Flying fish, rum cake and cricket, in that order. Bajan Rum Cake sells well anywhere far from here, and the farther the better.', options: [{label: 'Far away. Got it.', next: 'start'}]},
      ask: {text: 'My mother is ninety-four and has decided she would like to be ninety-three. I hear St. Augustine grows something called Fountain of Youth. Four bales, four hundred doubloons, and she will stop calling you skinny.', options: [
        {label: 'Anything for your mother.', do: 'quest:clementine', next: 'start'}, {label: 'Not today.', next: 'start'}]},
      done: {text: 'She is ninety-three already and out dancing! Four hundred doubloons, Captain, and a slice of cake for the road.', do: 'complete:clementine', options: [{label: 'Give her my best.', next: 'start'}]},
      treasure: {text: 'My grandfather swore a pirate buried a chest in the Tobago Cays, the little islands down in the Grenadines. He also swore he once outswam a shark, so take it how you like.', do: 'hint:tobagocays', options: [{label: 'I’ll take a look.', next: 'start'}]},
      again: {text: 'The Tobago Cays, down in the Grenadines, south of St. Vincent.', options: [{label: 'Thank you.', next: 'start'}]}
    }
  };

  /* Delivery requests: who asks, what for, and the reward. */
  var QUESTS = {
    percival:  {by: 'percival', port: 'portroyal', good: 'haze', n: 5, gold: 300},
    toussaint: {by: 'toussaint', port: 'petitgoave', good: 'mermaid', n: 2, gold: 350},
    catalina:  {by: 'catalina', port: 'havana', good: 'tangerine', n: 10, gold: 400},
    quill:     {by: 'quill', port: 'cartagena', good: 'kraken', n: 1, gold: 600},
    prudence:  {by: 'prudence', port: 'portobelo', good: 'cloud', n: 8, gold: 500},
    bartholomew: {by: 'bartholomew', port: 'staugustine', good: 'vanilla', n: 5, gold: 350},
    esperanza: {by: 'esperanza', port: 'veracruz', good: 'rumcake', n: 4, gold: 450},
    clementine: {by: 'clementine', port: 'barbados', good: 'fountain', n: 4, gold: 400}
  };

  var UPGRADES = {
    hold:     {name: 'Bigger hold', icon: '📦', levels: [20, 30, 45, 65, 90], cost: [400, 1200, 2800, 6000], note: 'Room for more bales.'},
    hull:     {name: 'Stouter hull', icon: '🛡️', levels: [30, 45, 65, 90], cost: [400, 1400, 3500], note: 'More hull points, so you last longer in a fight.'},
    cannons:  {name: 'More cannons', icon: '💣', levels: [0, 1, 2, 3, 4], cost: [300, 1000, 2600, 5500], note: 'Every broadside hits harder, and warning shots land better.'},
    crew:     {name: 'Hire boarders', icon: '👥', levels: [0, 1, 2, 3], cost: [400, 1300, 3200], note: 'Better odds when you board, and more hands to carry off loot.'},
    sails:    {name: 'Faster sails', icon: '⛵', levels: [0, 1, 2, 3], cost: [500, 1500, 3800], note: 'Sail faster, and outrun Customs and pirates more often.'},
    lavender: {name: 'Lavender-lined hold', icon: '🌸', levels: [0, 1], cost: [900], note: 'Customs can’t smell your cargo from as far away.'},
    secret:   {name: 'Smuggler’s hold', icon: '🕳️', levels: [0, 4, 10, 18], cost: [600, 1600, 3600],
      note: 'A hidden hold behind a false bulkhead, on top of your normal hold. Your most valuable bales ride in it: Customs never find them and pirates never take them.'}
  };

  /* Renown earns levels. Every level after the first gives a skill point. */
  var LEVELS = [
    {xp: 0, title: 'Deckhand'}, {xp: 60, title: 'Powder Monkey'}, {xp: 180, title: 'Bosun'}, {xp: 380, title: 'Navigator'},
    {xp: 680, title: 'Quartermaster'}, {xp: 1100, title: 'First Mate'}, {xp: 1650, title: 'Captain'}, {xp: 2350, title: 'Sea Wolf'},
    {xp: 3250, title: 'Commodore'}, {xp: 4400, title: 'Pirate Lord'}
  ];
  var SKILLS = {
    fight: {name: 'Fighting', icon: '⚔️', note: 'Harder broadsides and better boarding odds.'},
    sail:  {name: 'Sailing', icon: '🧭', note: 'A faster ship and better odds when you run.'},
    charm: {name: 'Charm', icon: '🗣️', note: 'Better prices, cheaper bribes and smoother talking.'}
  };
  var SKILL_MAX = 5;

  /* How rough each sea is: it sets how tough the pirates are and how rich the loot. */
  var SEA_TIER = {windward: 1, straits: 2, antilles: 2, gulf: 3, main: 3};
  var PIRATE_COUNT = {windward: 2, straits: 2, antilles: 2, gulf: 3, main: 3};
  // Pirate ships come in five sizes. Most match the sea they sail, some are bigger than you'd like.
  var SHIP_CLASS = ['sloop', 'brigantine', 'brig', 'frigate', 'man-o’-war'];
  var PIRATE_SHIPS = ['the Salty Grudge', 'the Crooked Grin', 'the Wet Sock', 'the Bad Idea', 'the Second Helping', 'the Loud Neighbour',
    'the Unpaid Invoice', 'the Sore Loser', 'the Petty Theft', 'the Last Straw'];
  var PIRATE_CAPTAINS = ['One-Eyed Edna Bramble', 'Barnaby “Bilge” Crumb', 'Scurvy Sal Tuckett', 'Gentleman Jeb Mortimer', 'Two-Hat Tilly Ross',
    'Ol’ Gums McGrady', 'Red Rosalind Fitch', 'Hobb the Nailbiter', 'Lady Winifred Rust', 'Short Pete Lomax'];
  var BOSS = {captain: 'Captain Silas Gristle', ship: 'the Bitter End', map: 'main', level: 7, gold: 2500, loot: {kraken: 3},
    intro: 'Black sails, red trim and a figurehead that is rude on purpose. Captain Silas Gristle, terror of the Spanish Main, has heard about you and does not like it.'};

  var CUSTOMS_NAMES = ['Lieutenant Dudley Clipboard', 'Ensign Agatha Stamp', 'Sergeant Percy Paperwork', 'Lieutenant Mabel Inkwell', 'Ensign Rupert Triplicate'];
  var MERCHANT_NAMES = ['the Prosperous Penny', 'the Comfortable Shoe', 'the Sensible Investment', 'the Mild Surprise', 'the Quarterly Report', 'the Reasonable Doubt', 'the Polite Cough'];

  /* Notes in bottles when no joke is to hand. */
  var BOTTLE_TIPS = [
    'The note reads: “Prices change every day. If a port won’t pay what you want, try again tomorrow, or try the next sea over.”',
    'The note reads: “Goods from another sea fetch the best prices. Tortuga Tangerine in Cartagena? Chef’s kiss.”',
    'The note reads: “Merchant ships carry Kraken Kush. Customs cutters carry clipboards. Choose your fights.”',
    'The note reads: “Black sails mean pirates. Pound them with broadsides first, then board when they’re weak.”',
    'The note reads: “Count the guns before you pick a fight. A frigate will send a sloop to the bottom. When the odds turn, run, pay or strike your colours.”',
    'The note reads: “Out of cannonballs? Lob a bale of Brick Weed. It hits softer, but their crew gets so high they can’t aim.”',
    'The note reads: “The sea keeps whatever sinks. Old Toussaint in Petit-Goâve rents out a cave where the sea can’t reach.”',
    'The note reads: “Whoever finds this: the haze over Serrana Bank never lifts. Signed, someone who got lost there for a week.”',
    'The note reads: “Pressed hash from Petit-Goâve fetches a fortune in Havana. Write down every price you see. Your ledger is your best friend.”',
    'The note reads: “Every strain gives a different buzz. Smoke a bale of Cartagena Candy before a tricky bit of business.”',
    'The note reads: “Every rope and sail on this ship is hemp. The word canvas comes from cannabis.” True, as it happens.',
    'The note reads: “Ship’s biscuit keeps for months if the weevils let it. Knock it on the table first.” Real sailors lived on hard biscuit, salt meat, beans and whatever fruit the last port sold.',
    'The note reads: “A fire ship is a hulk packed with tar and powder, steered at the enemy by a crew who jump for the boat at the last moment.” The English sent eight into the Spanish Armada off Calais in 1588, and Henry Morgan used one at Maracaibo in 1669.',
    'The note reads: “In 1692 an earthquake dropped half of Port Royal into the sea. Some say you can still hear the church bells.” The bells part is a legend; the earthquake is real.',
    'The note reads: “A letter of marque makes you a privateer: a pirate with paperwork. Get one, and pillaging the right flag is legal.”',
    'The note reads: “In 1717 King George offered a pardon to any pirate who gave it up within a year. Plenty took it. Some went straight back to sea.” A true story.',
    'The note reads: “Real captains flew false colours to sneak up close, then ran up their true flag before the first shot.”'
  ];

  /* Smoking (or eating) one bale gives a short boost for about two days of sailing. One boost at a time: a new one replaces the old.
     fight, sail, charm: extra skill points. luck: added to every odds check. sell: extra on every sale. speed: faster sailing.
     nose: how close Customs must get to smell you. calm: pirates leave you be. mend: 1 hull point a league. sight: see farther. comb: more floating bales. */
  var SMOKE = {
    tangerine: {name: 'Sunny Sails', sail: 2, does: '+2 Sailing: a faster ship and better odds when you run.', flavor: 'The whole deck smells like a sunny morning.'},
    purple:    {name: 'Pinky Out', charm: 2, does: '+2 Charm: better prices, cheaper bribes and smoother talking.', flavor: 'Everyone starts speaking very properly.'},
    breath:    {name: 'Old Sea Dog', fight: 2, does: '+2 Fighting: harder broadsides and better boarding odds.', flavor: 'Your crew starts growling at seagulls.'},
    haze:      {name: 'Low Profile', nose: 0.5, does: 'Customs have to sail twice as close to smell your cargo.', flavor: 'You feel smooth, slow and very hard to notice.'},
    nectar:    {name: 'Honey Hands', mend: 1, does: 'Your mellow crew patches 1 hull point for every league you sail.', flavor: 'Somebody starts humming and picks up a hammer.'},
    candy:     {name: 'Sugar Rush', luck: 0.1, does: '+10% on every odds check.', flavor: 'Everything feels like it’s going to work out.'},
    pineapple: {name: 'Party Hat', sell: 0.08, does: 'Buyers love you: +8% on everything you sell.', flavor: 'A tiny hat appears on your head. Nobody knows where from.'},
    cloud:     {name: 'Head in the Clouds', sight: 1.6, does: 'You see much farther, so the fog lifts faster.', flavor: 'The horizon looks very, very interesting.'},
    vanilla:   {name: 'Siesta', calm: 1, does: 'Pirates are too relaxed to bother you.', flavor: 'A great calm settles over the sea. Even the pirates yawn.'},
    fountain:  {name: 'Feeling Nineteen', sail: 1, charm: 1, fight: 1, does: '+1 Fighting, Sailing and Charm.', flavor: 'You feel young, bold and a bit reckless.'},
    rumcake:   {name: 'Beachcomber', comb: 1, does: 'Floating bales turn up twice as often.', flavor: 'You develop a keen eye for anything bobbing in the water.'},
    kraken:    {name: 'Eight Arms', fight: 2, sail: 2, charm: 2, luck: 0.1, does: '+2 to every skill and +10% on every odds check.', flavor: 'You feel like you could hold eight cutlasses at once.'},
    mermaid:   {name: 'Swims Like a Fish', speed: 0.25, does: 'Your ship sails 25% faster.', flavor: 'Salt spray, sweet air and a sudden urge to sing.'},
    hash:      {name: 'Iron Nerves', fight: 2, luck: 0.05, does: '+2 Fighting and +5% on every odds check.', flavor: 'Heavy, slow and steady. Nothing rattles you.'},
    rosin:     {name: 'Golden Glow', charm: 2, sell: 0.05, does: '+2 Charm and +5% on everything you sell.', flavor: 'You glow. Literally, a little. It’s fine.'},
    pearl:     {name: 'Dread Calm', fight: 3, luck: 0.05, does: '+3 Fighting and +5% on every odds check.', flavor: 'Dark, heavy and very quiet. You could stare down a hurricane.'},
    brick:     {name: 'Rough Night', fight: 1, does: '+1 Fighting. It isn’t pleasant, but it’s cheap.', flavor: 'Everyone coughs for ten minutes and then wants to fight a seagull.'},
    g_home:    {name: 'Garden Variety', charm: 1, does: '+1 Charm.', flavor: 'It tastes like a hillside. Everyone tells you how proud they are of you.'},
    g_nl:      {name: 'Lights Out', mend: 1, calm: 1, does: 'Pirates leave you be, and your sleepy crew patches 1 hull point for every league you sail.', flavor: 'Half the crew is asleep in the rigging. The other half is smiling at the stars.'},
    g_skunk:   {name: 'Skunk Cloud', fight: 2, sail: 1, does: '+2 Fighting and +1 Sailing.', flavor: 'The smell alone makes an enemy crew think twice.'},
    g_haze:    {name: 'Long Haze', sail: 2, sight: 1.6, does: '+2 Sailing, and you see much farther, so the fog lifts faster.', flavor: 'Every thought takes the scenic route, and the scenery is lovely.'},
    g_ak47:    {name: 'Quick Draw', fight: 2, luck: 0.05, does: '+2 Fighting and +5% on every odds check.', flavor: 'Sharp, fast and a little bit loud.'},
    g_shiva:   {name: 'Many Arms', fight: 3, does: '+3 Fighting.', flavor: 'Heavy and calm. You feel like you could hold a cutlass in every hand.'},
    g_ssh:     {name: 'Silver Tongue', charm: 3, sell: 0.05, does: '+3 Charm and +5% on everything you sell.', flavor: 'Everything you say comes out sounding clever. Some of it even is.'},
    g_jack:    {name: 'The Emperor’s Clothes', sail: 1, charm: 1, fight: 1, luck: 0.1, does: '+1 Fighting, Sailing and Charm, and +10% on every odds check.', flavor: 'Clear-headed, bright and ready for anything.'},
    biscuits:  {name: 'Slow Burn', sail: 1, charm: 1, fight: 1, days: 4, verb: 'eat', does: '+1 Fighting, Sailing and Charm, and it lasts twice as long.', flavor: 'Nothing happens for an hour. Then everything is lovely for days.'}
  };

  var PARROT = 'Admiral Biscuit';

  /* Your hideout: a cave on Île-à-Vache. What you leave there survives even if your ship goes down. */
  var HIDEOUT = {name: 'Île-à-Vache', map: 'windward', price: 500,
    caps: [40, 90, 160], capCost: [900, 2400]};

  /* Relics: one-of-a-kind finds that each goal can earn. They belong to the captain and go down with the ship. */
  var RELICS = {
    spyglass: {name: 'Brass Spyglass', icon: '🔭', sight: 1.4, does: 'You see 40% farther, so the fog lifts faster.'},
    tooth:    {name: 'Kraken Tooth', icon: '🦷', fight: 1, does: '+1 Fighting, for good.'},
    wig:      {name: 'Powdered Wig', icon: '🎩', charm: 1, does: '+1 Charm, for good.'},
    compass:  {name: 'Featherstone’s Compass', icon: '🧭', sail: 1, does: '+1 Sailing, for good.'},
    doubloon: {name: 'Lucky Doubloon', icon: '🪙', luck: 0.05, does: '+5% on every odds check.'},
    figure:   {name: 'Iron Figurehead', icon: '🗿', hull: 15, does: '+15 hull points, for good.'},
    seal:     {name: 'Merchant’s Seal', icon: '📜', sell: 0.05, does: '+5% on everything you sell.'},
    goldbrick:{name: 'Golden Brick', icon: '🧈', brick: 1, does: 'Brick Weed hits as hard as cannonballs.'},
    flag:     {name: 'Gristle’s Flag', icon: '🏴', scare: 2, does: 'Sloops and brigantines fly the other way when they see it.'}
  };

  /* Your ship's look. Some colours and flags are earned: each one says how. Earned ones stay earned for every voyage. */
  var SAILS = {
    canvas:  {name: 'Canvas', color: '#fbf4e2'},
    ochre:   {name: 'Ochre', color: '#e3b25a'},
    seafoam: {name: 'Sea green', color: '#8fd3b6'},
    sky:     {name: 'Sky blue', color: '#a9cfee'},
    rose:    {name: 'Rose', color: '#f0a7b6'},
    black:   {name: 'Black', color: '#2b2b2b', earn: 'Beat a pirate ship'},
    crimson: {name: 'Crimson', color: '#b8322a', earn: 'Beat a frigate or a man-o’-war'},
    gold:    {name: 'Gold', color: '#f2c94c', earn: 'Have 5,000 doubloons at once'},
    emerald: {name: 'Emerald', color: '#2fae6b', earn: 'Dig up the Emerald Bale'}
  };
  var FLAGS = {
    skull:  {name: 'Skull and crossbones', icon: '☠️', color: '#141414'},
    leaf:   {name: 'Green leaf', icon: '🌿', color: '#2f8f4e'},
    parrot: {name: 'Parrot', icon: '🦜', color: '#d0342c'},
    anchor: {name: 'Anchor', icon: '⚓', color: '#24446e'},
    kraken: {name: 'Kraken', icon: '🐙', color: '#6b3fa0', earn: 'Get hold of Kraken Kush'},
    crown:  {name: 'Stolen crown', icon: '👑', color: '#c99a1d', earn: 'Reach level 10'}
  };


  /* ---------- The powers of 1718 ----------
     The game is set in 1718: Nassau's pirate republic is in its last summer, and Britain and France are squaring up to Spain
     (the War of the Quadruple Alliance, 1718 to 1720). Flags and facts are real; every officer, ship and captain is made up. */
  var NATIONS = {
    britain: {name: 'Great Britain', short: 'Britain', adj: 'British', law: 'His Majesty’s Customs', navy: 'the Royal Navy',
      flag: 'The red ensign, with the new Union flag of 1707 in the corner.',
      officers: ['Lieutenant Dudley Clipboard', 'Ensign Agatha Stamp', 'Sergeant Percy Paperwork', 'Lieutenant Mabel Inkwell', 'Ensign Rupert Triplicate'],
      ships: ['HMS Stern Rebuke', 'HMS Proper Channels', 'HMS Strongly Worded', 'HMS Unamused'],
      captains: ['Captain Aldous Throgmorton', 'Captain Euphemia Starch', 'Captain Bertram Sternwell']},
    spain: {name: 'Spain', short: 'Spain', adj: 'Spanish', law: 'the guarda costa', navy: 'the Spanish Armada',
      flag: 'White, with the king’s arms. The old Cross of Burgundy, a ragged red X on white, still flew beside it until 1785.',
      officers: ['Teniente Bartolo Sello', 'Alférez Inés Papeleo', 'Sargento Lucía Expediente', 'Capitán Tomás Trámite'],
      ships: ['Nuestra Señora del Sello', 'San Trámite', 'Santa Paciencia', 'La Ventanilla'],
      captains: ['Don Rodrigo de la Ventanilla', 'Doña Eulalia de los Sellos', 'Don Fermín Expediente']},
    france: {name: 'France', short: 'France', adj: 'French', law: 'the King’s customs', navy: 'the French royal navy',
      flag: 'Plain white, sometimes strewn with gold lilies.',
      officers: ['Enseigne Margot Paperasse', 'Lieutenant Gaston Tampon', 'Sergent Odile Formulaire'],
      ships: ['Le Formidable Formulaire', 'La Paperasse', 'Le Tampon Royal'],
      captains: ['Capitaine Aristide Tampon', 'Capitaine Hortense Paperasse']},
    dutch: {name: 'the Dutch Republic', short: 'the Dutch', adj: 'Dutch', law: 'the Company’s customs', navy: 'the Dutch navy',
      flag: 'Red, white and blue stripes. In Curaçao the Dutch West India Company ran things.',
      officers: ['Luitenant Pieter Stempel', 'Vaandrig Femke Formulier', 'Schout Joost Papierwerk'],
      ships: ['Zeven Stempels', 'De Nette Boekhouder', 'Het Formulier'],
      captains: ['Kapitein Willem Boekhouder', 'Kapitein Grietje Stempel']},
    brethren: {name: 'the Brethren of the Coast', short: 'the Brethren', adj: 'pirate', law: 'nobody', navy: 'nobody',
      flag: 'Black, with skulls, bones and hourglasses. The name “Jolly Roger” turns up in print in the 1720s.',
      officers: [], ships: [], captains: []}
  };
  var NATION_ORDER = ['britain', 'spain', 'france', 'dutch', 'brethren'];
  // Who is at war with whom in 1718. The Dutch stayed out of the fighting and kept trading.
  var WAR = {britain: ['spain'], france: ['spain'], spain: ['britain', 'france'], dutch: [], brethren: []};
  var WAR_NOTE = 'Britain and France are squaring up to Spain (the War of the Quadruple Alliance, 1718 to 1720). The Dutch keep their heads down and keep trading.';
  // Whose customs patrol each sea, whose warships sail it, and whose merchantmen trade there.
  var SEA_LAW = {windward: 'britain', straits: 'spain', gulf: 'spain', main: 'spain', antilles: 'britain'};
  var SEA_NAVY = {windward: ['britain'], straits: ['spain'], gulf: ['spain'], main: ['spain', 'dutch'], antilles: ['britain', 'france']};
  var SEA_TRADE = {windward: ['britain', 'france', 'spain'], straits: ['spain', 'britain'], gulf: ['spain'], main: ['spain', 'dutch'], antilles: ['britain', 'france', 'dutch']};
  // Navy warships come in three sizes (tier 3 to 5).
  var NAVY_CLASS = ['sloop of war', 'frigate', 'ship of the line'];
  // Standing with each nation, from -100 to 100, sorted into five tiers. sell and buy scale prices in its ports,
  // bribe scales what its customs want, law scales how often and how keenly its customs bother you, pay adds to its job rewards.
  var STAND = [
    {name: 'Hostile', icon: '🔴', sell: 0.92, buy: 1.08, bribe: 2, law: 1.6, pay: 0},
    {name: 'Wary', icon: '🟠', sell: 0.96, buy: 1.04, bribe: 1.5, law: 1.3, pay: 0},
    {name: 'Neutral', icon: '⚪', sell: 1, buy: 1, bribe: 1, law: 1, pay: 0},
    {name: 'Friendly', icon: '🟢', sell: 1.03, buy: 0.97, bribe: 0.75, law: 0.8, pay: 0.1},
    {name: 'Honoured', icon: '🌟', sell: 1.06, buy: 0.94, bribe: 0.5, law: 0.5, pay: 0.2}
  ];

  /* Whose flag flies over each port in 1718, and one true line of its history. */
  var PORT_INFO = {
    tortuga: {nation: 'france', history: 'Tortuga was the buccaneers’ favourite hideout from the 1630s. By 1718 it is a quiet corner of French Saint-Domingue, and the buccaneers have mostly moved on.'},
    portroyal: {nation: 'britain', history: 'Henry Morgan sailed from Port Royal in the 1660s. In 1692 an earthquake dropped half the town into the harbour, and Kingston grew up across the bay.'},
    petitgoave: {nation: 'france', history: 'Petit-Goâve was a buccaneer harbour on the French side of Hispaniola. Spain signed that side over to France in 1697.'},
    havana: {nation: 'spain', history: 'Spain’s treasure fleets gathered in Havana before crossing to Spain, so the harbour has some of the strongest forts in the Americas.'},
    nassau: {nation: 'brethren', history: 'From about 1706 to 1718 Nassau was a pirate republic: Blackbeard, Charles Vane and Sam Bellamy all drank here. Woodes Rogers arrives in July 1718 with the King’s pardon.'},
    cartagena: {nation: 'spain', history: 'Francis Drake captured Cartagena in 1586 and only left once the city paid a huge ransom. Spain answered with walls you can still walk on.'},
    portobelo: {nation: 'spain', history: 'Peru’s silver came to Portobelo’s great trade fairs. Henry Morgan raided the town in 1668.'},
    willemstad: {nation: 'dutch', history: 'The Dutch took Curaçao in 1634, and the Dutch West India Company made Willemstad one of the busiest trading ports in the Caribbean.'},
    staugustine: {nation: 'spain', history: 'Founded in 1565, St. Augustine is the oldest town on the US mainland that Europeans founded and people have lived in ever since.'},
    veracruz: {nation: 'spain', history: 'Veracruz was New Spain’s main port. In 1683 the buccaneers Laurens de Graaf and Michel de Grammont sacked it.'},
    barbados: {nation: 'britain', history: 'The English settled Barbados in 1627. In 1717 Stede Bonnet, a well-off Barbados gentleman, bought a sloop and turned pirate, to everyone’s surprise.'}
  };
  for (var pi in PORT_INFO) if (PORTS[pi]) { PORTS[pi].nation = PORT_INFO[pi].nation; PORTS[pi].history = PORT_INFO[pi].history; }

  /* The job board. Plain cargo for deliveries: none of it is weed. */
  var JOB_CARGO = ['crates of nails and lamp oil', 'coils of hemp rope', 'bolts of hemp sailcloth', 'crates of books and letters',
    'casks of fresh water', 'crates of cooking pots', 'barrels of tar'];
  // Harbour news. {port}, {good}, {sea} and {law} are filled in.
  var NEWS = {
    spike: ['A navy squadron just dropped anchor in {port}, and every sailor ashore wants {good}.', 'There’s a big wedding in {port}. The guests want {good}, and lots of it.',
      'A storm sank the boat that brings {good} to {port}. Buyers there are desperate.'],
    glut: ['A bumper crop of {good} in {port}: the market is swimming in it.', 'Too many ships brought {good} to {port}. Prices there have fallen through the deck.'],
    crack: ['A new governor wants to look tough: {law} have doubled their patrols in {sea}.', 'Word is {law} are stopping every hull in {sea} this week.'],
    raid: ['Pirates are thick in {sea}. Three ships were taken this week.', 'A pirate crew has set up shop in {sea}. Sail careful.']
  };
  // What each level opens up, so the start stays simple.
  var UNLOCK = {
    2: 'Jobs, harbour news and provisions. Port taverns now post paid jobs (📋 Jobs) and the news moves prices. Your crew starts eating too: a day’s rations for every day at sea, and two more every time you smoke (the munchies). Buy provisions in any market. A hungry crew sails slower and does everything worse.',
    3: 'Bounties, letters of marque and decoys. Hunt wanted pirates for a nation, or carry its papers and pillage its enemies legally. Shipwrights now sell decoy sloops that sail in your wake and lead trouble away from you.',
    4: 'Fire ships. Taverns in Nassau, Tortuga, Petit-Goâve and Port Royal can find you a fire ship: an old hulk packed with tar and powder to send into one enemy ship. Her skeleton crew rows clear before she hits.'
  };
  // Fire ships: where to hire one, and the real story behind it.
  var FIRE_PORTS = ['nassau', 'tortuga', 'petitgoave', 'portroyal'];
  var FIRESHIP_NOTE = 'In 1669 three Spanish warships trapped Henry Morgan inside Lake Maracaibo. He disguised a captured ship as a warship, packed her with tar, powder and brimstone, and sent her into the Spanish flagship Magdalena, which burned. Her few crew got clear just before she struck, and Morgan’s fleet slipped out to sea.';

  /* The grow: two beds above the hideout. Landrace seeds come from three tavern seed traders; crosses are real,
     documented breeding lines (simplified to one pair at a time). Seeds you buy or breed stay in the seed chest for good. */
  var GROW = {days: 6, yield: 6, beds: 2, price: 120, xp: 60};
  var GENES = {
    afghani:  {name: 'Afghani', kind: 'landrace', from: 'willemstad', note: 'A landrace from the Hindu Kush mountains: short, broad-leafed, sticky with resin and quick to flower.'},
    thai:     {name: 'Thai', kind: 'landrace', from: 'willemstad', note: 'A landrace from Thailand: tall, narrow-leafed and slow, with a bright, racy high.'},
    sindian:  {name: 'South Indian', kind: 'landrace', from: 'willemstad', note: 'A landrace from southern India: tall and slow to finish, grown there for centuries.'},
    colgold:  {name: 'Colombian Gold', kind: 'landrace', from: 'cartagena', note: 'A landrace from Colombia’s Santa Marta mountains: tall, golden and strong.'},
    acapulco: {name: 'Acapulco Gold', kind: 'landrace', from: 'veracruz', note: 'A landrace from Mexico’s Pacific coast: tall, gold-tinged and famous by name.'},
    x_afcol:  {name: 'Afghani × Colombian Gold', kind: 'cross', note: 'Halfway to Skunk #1. Cross it with Acapulco Gold.'},
    x_mexcol: {name: 'Acapulco Gold × Colombian Gold', kind: 'cross', note: 'The start of both Haze and AK-47.'},
    x_mcsi:   {name: 'Mexican × Colombian × South Indian', kind: 'cross', note: 'One step from Haze. Cross it with Thai.'},
    x_mct:    {name: 'Colombian × Mexican × Thai', kind: 'cross', note: 'One step from AK-47. Cross it with Afghani.'},
    x_hznl:   {name: 'Haze × Northern Lights', kind: 'cross', note: 'One step from Jack Herer. Cross it with Shiva Skunk.'},
    nl:       {name: 'Northern Lights', kind: 'strain', good: 'g_nl', note: 'Usually described as Afghani × Thai. It came out of the US Pacific Northwest in the 1970s and was made famous by a Dutch seed bank in the 1980s.'},
    skunk1:   {name: 'Skunk #1', kind: 'strain', good: 'g_skunk', note: 'Afghani × Colombian Gold, crossed again with Acapulco Gold, in 1970s California. It won the first High Times Cannabis Cup in 1988 and sits in the family tree of countless modern strains.'},
    haze:     {name: 'Original Haze', kind: 'strain', good: 'g_haze', note: 'Bred in Santa Cruz, California, in the 1970s from Mexican, Colombian, South Indian and Thai landraces. The exact recipe is part legend.'},
    ak47:     {name: 'AK-47', kind: 'strain', good: 'g_ak47', note: 'Released by Serious Seeds in 1992 from Colombian, Mexican, Thai and Afghani genetics. The breeder never published the order of the crosses.'},
    shiva:    {name: 'Shiva Skunk', kind: 'strain', good: 'g_shiva', note: 'Northern Lights #5 × Skunk #1, first sold in 1987 and renamed Shiva Skunk a few years later.'},
    ssh:      {name: 'Super Silver Haze', kind: 'strain', good: 'g_ssh', note: 'Skunk, Northern Lights and Haze. It won the High Times Cannabis Cup three years running, 1997 to 1999.'},
    jack:     {name: 'Jack Herer', kind: 'strain', good: 'g_jack', note: 'Sensi Seeds keeps the recipe secret, but growers believe it’s Haze, Northern Lights #5 and Shiva Skunk. It’s named after the hemp activist who wrote The Emperor Wears No Clothes (1985).'}
  };
  // Each pair, in either order, and what its seeds grow into.
  var CROSSES = [
    ['afghani', 'thai', 'nl'], ['afghani', 'colgold', 'x_afcol'], ['x_afcol', 'acapulco', 'skunk1'],
    ['acapulco', 'colgold', 'x_mexcol'], ['x_mexcol', 'sindian', 'x_mcsi'], ['x_mcsi', 'thai', 'haze'],
    ['x_mexcol', 'thai', 'x_mct'], ['x_mct', 'afghani', 'ak47'],
    ['nl', 'skunk1', 'shiva'], ['shiva', 'haze', 'ssh'], ['haze', 'nl', 'x_hznl'], ['x_hznl', 'shiva', 'jack']
  ];
  var GROW_LESSONS = [
    'A landrace is a local variety that adapted to one place over many generations of farmers saving their own seed.',
    'Crossing two plants mixes their genes. Real breeders grow out hundreds of seedlings, keep the best and cross again for years before a strain grows true.',
    'Afghani-type plants grow short and finish fast. Thai, Colombian and Mexican types grow tall and take far longer. Most famous hybrids mix the two.',
    'The labels indica and sativa describe how a plant grows. Lab tests show they say much less about how it feels.'
  ];

  // The MJBizCon week board (Las Vegas Convention Center, December 1 to 4, 2026). Times are UTC: it closes at the end of
  // Sunday, December 6 in Las Vegas and leaves the title screen at the new year.
  var BOARD = {name: 'MJBizCon week', open: Date.UTC(2026, 10, 26), close: Date.UTC(2026, 11, 7, 8), hide: Date.UTC(2027, 0, 1, 8), max: 30,
    url: 'https://the-reefer.com/pillage/',
    blurb: 'For MJBizCon in Las Vegas, December 1 to 4. Show another player your score’s QR code, or send them the link, and you land on each other’s boards. Your best voyage until December 6 counts.',
    // Whoever tops the overall board.
    top: 'Admiral of the Week',
    // The breakout boards: one for each thing the game counts, and a title for whoever leads it. Each player's best
    // from any voyage this week counts. Shared score codes carry these in this order, so only ever add to the end.
    stats: [
      {k: 'sold', icon: '📦', board: 'Top Smugglers', one: 'bale sold', many: 'bales sold', crown: 'Smuggler Supreme', how: 'Sell a bale in any market.'},
      {k: 'smoked', icon: '💨', board: 'Most Smoked', one: 'bale smoked', many: 'bales smoked', crown: 'Captain Cloud', how: 'Light up a bale from your hold.'},
      {k: 'pillaged', icon: '⚓', board: 'Merchant Wreckers', one: 'merchant plundered', many: 'merchants plundered', crown: 'Scourge of the Merchant Fleet', how: 'Plunder a merchant ship.'},
      {k: 'sunk', icon: '💥', board: 'Pirate Hunters', one: 'pirate ship sunk', many: 'pirate ships sunk', crown: 'Terror of the Brethren', how: 'Sink a pirate ship.'},
      {k: 'dug', icon: '💎', board: 'Treasure Hounds', one: 'treasure dug up', many: 'treasures dug up', crown: 'X Marks the Spot', how: 'Dig up buried treasure.'},
      {k: 'bricks', icon: '🧱', board: 'Brick Lobbers', one: 'bale of Brick Weed lobbed', many: 'bales of Brick Weed lobbed', crown: 'Commodore of Bricks', how: 'Lob Brick Weed in a fight.'},
      {k: 'days', icon: '🧭', board: 'Old Salts', one: 'day at sea', many: 'days at sea', crown: 'Saltiest Dog', how: 'Spend a day at sea.'}
    ]};

  /* Real geography: every sea's coastline, crossings and sea lanes, and where each port, dig site and the hideout sit. */
  var C = window.PILLAGE_COASTS;
  Object.keys(MAPS).forEach(function (mid) { var sea = C.seas[mid]; for (var k in sea) MAPS[mid][k] = sea[k]; });
  Object.keys(PORTS).forEach(function (pid) { var p = C.ports[pid]; PORTS[pid].dock = p.dock; PORTS[pid].town = p.town; PORTS[pid].ll = p.ll; });
  Object.keys(STASHES).forEach(function (sid) { STASHES[sid].at = C.stashes[sid].at; STASHES[sid].ll = C.stashes[sid].ll; });
  HIDEOUT.at = C.hideout.at; HIDEOUT.dock = C.hideout.dock; HIDEOUT.ll = C.hideout.ll;

  window.PILLAGE_DATA = {GOODS: GOODS, COMMON: COMMON, MAPS: MAPS, PORTS: PORTS, STASHES: STASHES, PEOPLE: PEOPLE,
    QUESTS: QUESTS, UPGRADES: UPGRADES, LEVELS: LEVELS, SKILLS: SKILLS, SKILL_MAX: SKILL_MAX, SEA_TIER: SEA_TIER,
    PIRATE_COUNT: PIRATE_COUNT, PIRATE_SHIPS: PIRATE_SHIPS, PIRATE_CAPTAINS: PIRATE_CAPTAINS, BOSS: BOSS,
    CUSTOMS_NAMES: CUSTOMS_NAMES, MERCHANT_NAMES: MERCHANT_NAMES, BOTTLE_TIPS: BOTTLE_TIPS, SMOKE: SMOKE, PARROT: PARROT,
    SHIP_CLASS: SHIP_CLASS, HIDEOUT: HIDEOUT, RELICS: RELICS, SAILS: SAILS, FLAGS: FLAGS,
    NATIONS: NATIONS, NATION_ORDER: NATION_ORDER, WAR: WAR, WAR_NOTE: WAR_NOTE, SEA_LAW: SEA_LAW, SEA_NAVY: SEA_NAVY, SEA_TRADE: SEA_TRADE,
    NAVY_CLASS: NAVY_CLASS, STAND: STAND, JOB_CARGO: JOB_CARGO, NEWS: NEWS, UNLOCK: UNLOCK, FIRE_PORTS: FIRE_PORTS, FIRESHIP_NOTE: FIRESHIP_NOTE,
    GROW: GROW, GENES: GENES, CROSSES: CROSSES, GROW_LESSONS: GROW_LESSONS, BOARD: BOARD, SCALE: C.k};
})();
