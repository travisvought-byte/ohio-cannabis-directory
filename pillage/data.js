/* Pillage the Reefer: the seas, ports, cargo and people.
   Original characters and writing. Ports are real old Caribbean harbors; the strains, people and Smoke Cay are made up. */
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
    kraken:    {name: 'Kraken Kush', icon: '🐙', base: 150, rare: 'Only found in the holds of merchant ships.', note: 'Legendary. Grips you with all eight arms.'},
    mermaid:   {name: "Mermaid's Kiss", icon: '🧜', base: 120, rare: 'Only found floating at sea.', note: 'Drifts in on the tide, sweet and salty.'}
  };
  var COMMON = ['tangerine', 'purple', 'breath', 'haze', 'nectar', 'candy', 'pineapple', 'cloud'];

  /* Land shapes, in map units. ribbon: a spine of [x, y, half-width]; blob: centre, radii, turn, seed; poly: an outline. */
  var MAPS = {
    windward: {
      name: 'The Windward Passage', short: 'Windward Passage', w: 1600, h: 1100,
      blurb: 'Between Cuba, Hispaniola and Jamaica. Home waters.',
      lands: [
        {name: 'Cuba', label: [330, 286], ribbon: [[-140, 250, 76], [100, 262, 80], [320, 285, 72], [520, 318, 60], [680, 350, 42], [790, 378, 14]]},
        {name: 'Hispaniola', label: [1300, 470], poly: [[880, 402], [945, 362], [1050, 332], [1200, 316], [1350, 320], [1500, 330], [1680, 340], [1680, 700], [1450, 690], [1250, 680], [1100, 692], [980, 702], [880, 708], [800, 712], [786, 690], [860, 662], [950, 642], [1010, 602], [1032, 540], [1000, 500], [950, 470], [905, 440]]},
        {name: 'Gonâve', blob: [925, 548, 48, 15, -0.15, 3]},
        {name: 'Tortuga', blob: [1000, 268, 58, 15, -0.05, 7]},
        {name: 'Jamaica', label: [410, 745], ribbon: [[250, 745, 30], [330, 735, 40], [430, 745, 45], [520, 765, 38], [585, 785, 20]]},
        {name: 'Navassa', blob: [705, 760, 14, 10, 0, 11]},
        {name: 'Great Inagua', label: [930, 115], blob: [930, 115, 65, 28, 0.1, 5]},
        {name: 'Little Inagua', blob: [1045, 92, 22, 12, 0.2, 6]},
        {name: 'Caicos', blob: [1460, 90, 52, 22, -0.1, 9]},
        {name: 'Île-à-Vache', blob: [960, 738, 14, 6, 0.1, 13]},
        {name: 'Morant Cays', blob: [655, 880, 10, 5, 0.3, 15]},
        {name: 'Pedro Cays', blob: [330, 885, 14, 5, -0.2, 17]},
        {name: 'Cayman Brac', blob: [70, 640, 20, 6, 0.15, 19]}
      ],
      exits: [
        {to: 'straits', rect: [0, 20, 36, 140], label: 'To the Florida Straits', at: [10, 80], arrive: [1530, 740]},
        {to: 'main', rect: [60, 1066, 1480, 34], label: 'To the Spanish Main', at: [800, 1088], arrive: ['x', 60]}
      ],
      arrive: {straits: [60, 90], main: ['x', 1030]},
      patrols: [
        {kind: 'customs', route: [[700, 520], [880, 470], [1150, 250], [1350, 260], [880, 470], [620, 900], [300, 900], [460, 560]]},
        {kind: 'merchant', route: [[100, 560], [700, 610], [1250, 840], [1550, 960], [700, 960], [120, 640]]}
      ]
    },
    straits: {
      name: 'The Florida Straits', short: 'Florida Straits', w: 1600, h: 1100,
      blurb: 'Havana, Nassau and a thousand little cays.',
      lands: [
        {name: 'Cuba', label: [800, 900], ribbon: [[-140, 900, 62], [150, 880, 70], [380, 835, 60], [600, 815, 70], [850, 830, 78], [1100, 860, 80], [1350, 885, 80], [1720, 905, 80]]},
        {name: 'Florida', label: [215, 150], poly: [[-60, -60], [430, -60], [445, 60], [430, 170], [395, 265], [345, 330], [280, 352], [200, 330], [120, 265], [40, 225], [-60, 215]]},
        {name: 'The Keys', blob: [305, 386, 15, 5, 0.6, 21]},
        {name: 'The Keys', blob: [262, 412, 17, 5, 0.35, 22]},
        {name: 'The Keys', blob: [215, 432, 16, 5, 0.2, 23]},
        {name: 'The Keys', blob: [168, 446, 14, 4, 0.1, 24]},
        {name: 'The Keys', blob: [122, 454, 12, 4, 0, 25]},
        {name: 'Dry Tortugas', blob: [52, 480, 10, 7, 0, 26]},
        {name: 'Andros', label: [1000, 450], blob: [1000, 450, 55, 125, 0.12, 31]},
        {name: 'New Providence', blob: [1135, 335, 38, 15, 0, 33]},
        {name: 'Eleuthera', ribbon: [[1225, 250, 9], [1270, 300, 12], [1305, 370, 11], [1315, 450, 9], [1300, 520, 7]]},
        {name: 'Grand Bahama', ribbon: [[690, 140, 14], [800, 150, 18], [920, 140, 16], [1000, 118, 10]]},
        {name: 'Abaco', blob: [1125, 140, 35, 70, 0.3, 41]},
        {name: 'Bimini', blob: [700, 330, 9, 14, 0, 43]},
        {name: 'Cay Sal', blob: [690, 620, 16, 10, 0, 45]},
        {name: 'Exumas', blob: [1210, 560, 10, 6, 0.5, 46]},
        {name: 'Exumas', blob: [1240, 600, 12, 6, 0.6, 47]},
        {name: 'Exumas', blob: [1270, 640, 10, 5, 0.6, 48]},
        {name: 'Long Island', ribbon: [[1400, 500, 8], [1430, 580, 10], [1460, 650, 7]]}
      ],
      exits: [
        {to: 'windward', rect: [1564, 690, 36, 110], label: 'To the Windward Passage', at: [1590, 745], arrive: [60, 90]}
      ],
      arrive: {windward: [1530, 740]},
      patrols: [
        {kind: 'customs', route: [[300, 700], [700, 700], [620, 470], [380, 560]]},
        {kind: 'customs', route: [[1200, 400], [1380, 700], [900, 720], [860, 300]]},
        {kind: 'merchant', route: [[100, 620], [600, 700], [1000, 690], [1500, 760], [1100, 250], [500, 450]]}
      ]
    },
    main: {
      name: 'The Spanish Main', short: 'Spanish Main', w: 1600, h: 1100,
      blurb: 'Old treasure ports along the South American coast.',
      lands: [
        {name: 'South America', label: [1150, 900], poly: [[-60, 1160], [-60, 700], [70, 712], [190, 755], [290, 798], [370, 858], [425, 832], [505, 792], [590, 742], [690, 700], [810, 640], [895, 560], [945, 590], [960, 700], [985, 805], [1055, 800], [1075, 705], [1125, 640], [1175, 700], [1300, 722], [1450, 705], [1660, 722], [1660, 1160]]},
        {name: 'Curaçao', blob: [1190, 470, 44, 13, -0.35, 51]},
        {name: 'Aruba', blob: [1060, 505, 22, 8, -0.4, 53]},
        {name: 'Bonaire', blob: [1300, 445, 24, 11, 0.5, 55]},
        {name: 'Providencia', blob: [110, 250, 13, 16, 0, 57]},
        {name: 'San Andrés', blob: [70, 362, 8, 14, 0, 59]},
        {name: 'Rosario Islands', blob: [440, 735, 12, 5, 0.2, 61]},
        {name: 'Smoke Cay', label: [760, 300], blob: [760, 300, 34, 22, 0.3, 63], haze: true},
        {name: 'Margarita', blob: [1555, 560, 40, 16, 0, 65]},
        {name: 'Los Roques', blob: [1440, 470, 14, 6, 0.3, 67]},
        {name: 'Serrana Bank', blob: [330, 150, 15, 6, -0.3, 69]},
        {name: 'Roncador', blob: [230, 330, 8, 5, 0, 71]},
        {name: 'Isla de Aves', blob: [1480, 200, 9, 5, 0.4, 73]}
      ],
      exits: [
        {to: 'windward', rect: [60, 0, 1480, 34], label: 'To the Windward Passage', at: [800, 12], arrive: ['x', 1030]}
      ],
      arrive: {windward: ['x', 60]},
      patrols: [
        {kind: 'customs', route: [[300, 650], [700, 600], [1000, 420], [1300, 560], [700, 420]]},
        {kind: 'merchant', route: [[100, 500], [600, 520], [1100, 380], [1500, 640], [850, 480], [300, 420]]}
      ]
    }
  };

  /* Ports. dock: where the ship ties up (water); town: where the houses are drawn (land). */
  var PORTS = {
    tortuga:    {name: 'Tortuga', map: 'windward', dock: [1000, 302], town: [1000, 272], sells: ['tangerine', 'breath', 'purple'], yard: true, who: 'ruthie',
                 blurb: 'A rocky little island full of hammocks, gossip and suspicious-smelling smoke.'},
    portroyal:  {name: 'Port Royal', map: 'windward', dock: [545, 832], town: [532, 798], sells: ['purple', 'tangerine', 'haze'], yard: true, who: 'percival',
                 blurb: 'The richest, rowdiest harbor in the Caribbean. The wigs are very tall here.'},
    petitgoave: {name: 'Petit-Goâve', map: 'windward', dock: [985, 598], town: [994, 630], sells: ['breath', 'tangerine', 'pineapple'], yard: false, who: 'toussaint',
                 blurb: 'A quiet old buccaneer harbor where everyone is mending a net or pretending to.'},
    havana:     {name: 'Havana', map: 'straits', dock: [385, 746], town: [385, 792], sells: ['haze', 'nectar', 'purple'], yard: true, who: 'catalina',
                 blurb: 'Grand walls, grand ships and the finest rollers on any sea.'},
    nassau:     {name: 'Nassau', map: 'straits', dock: [1132, 300], town: [1135, 334], sells: ['nectar', 'haze', 'tangerine'], yard: false, who: 'mildew',
                 blurb: 'A pirate republic of palm trees, hammocks and very relaxed rules.'},
    cartagena:  {name: 'Cartagena', map: 'main', dock: [500, 758], town: [508, 806], sells: ['candy', 'pineapple', 'cloud'], yard: true, who: 'quill',
                 blurb: 'A walled city of balconies, bells and one very busy botanist.'},
    portobelo:  {name: 'Portobelo', map: 'main', dock: [180, 724], town: [182, 770], sells: ['pineapple', 'candy', 'breath'], yard: false, who: 'prudence',
                 blurb: 'Sleepy treasure port. Somebody important is on holiday here.'},
    willemstad: {name: 'Willemstad', map: 'main', dock: [1196, 502], town: [1192, 472], sells: ['cloud', 'candy', 'nectar'], yard: true, who: 'ines',
                 blurb: 'Colorful houses, a floating bridge and a famous captain in retirement.'}
  };

  /* Buried treasure. A rumor marks the spot on your chart; the Emerald Bale needs all three map pieces. */
  var STASHES = {
    s1: {name: 'Navassa', map: 'windward', at: [705, 760], piece: true, gold: 150, loot: {mermaid: 3},
         text: 'You dig past three goats and one very offended crab. Clunk! A chest! Inside: the first piece of Captain Featherstone’s map, 150 doubloons and 3 bales of Mermaid’s Kiss.'},
    s2: {name: 'the Dry Tortugas', map: 'straits', at: [52, 480], piece: true, gold: 250, loot: {kraken: 1},
         text: 'Under a palm tree shaped like a question mark you find the second piece of the map, 250 doubloons and a bale of Kraken Kush.'},
    s3: {name: 'Providencia', map: 'main', at: [110, 250], piece: true, gold: 300, loot: {kraken: 2},
         text: 'Behind a rock that looks like a sleeping landlord: the third piece of the map, 300 doubloons and 2 bales of Kraken Kush.'},
    emerald: {name: 'Smoke Cay', map: 'main', at: [760, 300], needs: 3, gold: 2000, loot: {},
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
        {label: 'Just passing through.', end: true}]},
      trade: {text: 'Buy it cheap where it grows, sell it dear where it doesn’t. Tortuga Tangerine grows like a weed here, mostly because it is one. Haul it somewhere fancy, like Port Royal or Havana, and watch the coin roll in.', options: [{label: 'Buy low, sell high. Got it.', next: 'start'}]},
      rumor: {text: 'Old Captain Ines Featherstone grew the finest crop that ever sailed: the Emerald Bale. Before she retired she buried it and tore her map in three. One piece is on Navassa, a lonely rock south-west of here. Only goats live there. Very judgmental goats.', do: 'hint:s1', options: [{label: 'I’ll go have a look.', next: 'start'}]},
      rumor2: {text: 'Navassa, love. South-west, between here and Jamaica. Follow the smell of goat.', options: [{label: 'Thanks, Ruthie.', next: 'start'}]},
      where: {text: 'Sail west past the tip of Cuba for the Florida Straits: Havana and Nassau. Sail off the bottom of the chart for the Spanish Main: Cartagena and friends. And mind the Crown Customs cutters. Blue sails. No sense of humor.', do: 'know:havana,know:cartagena', options: [{label: 'Blue sails. Noted.', next: 'start'}]}
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
        {label: 'Farewell, Grandpère.', end: true}]},
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
      teach: {text: 'No. But I will tell you this for free: Havana pays well for Port Royal Purple, and the Customs cutters here are thick as mosquitoes. Pay them, outrun them or outsmart them. Never cry in front of them. Oh, and Nassau buys anything. Anything.', do: 'know:nassau', options: [{label: 'No crying. Understood.', next: 'start'}]},
      ask: {text: 'Ten bales of Tortuga Tangerine. I am experimenting with citrus notes. Four hundred doubloons.', options: [
        {label: 'Consider it done.', do: 'quest:catalina', next: 'start'}, {label: 'Another time.', next: 'start'}]},
      done: {text: 'Perfect. Bright as a sunrise. Four hundred doubloons, and you may now touch exactly one thing on my table. Not that one.', do: 'complete:catalina', options: [{label: 'Gracias.', next: 'start'}]}
    },
    mildew: {
      name: 'Captain Mildred “Mildew” Mudge', role: 'Retired pirate, professional hammock tester', icon: '🏝️', port: 'nassau',
      start: {text: 'Shh. I’m resting. I’ve been resting for about thirty years. Big job, resting.', options: [
        {label: 'Any treasure around here?', next: 'treasure', if: '!hint:s2'},
        {label: 'Where was that treasure again?', next: 'again', if: 'hint:s2'},
        {label: 'Why do they call you Mildew?', next: 'name'},
        {label: 'Sweet dreams.', end: true}]},
      treasure: {text: 'Mmh. Ines Featherstone hid a piece of her map on the Dry Tortugas, way out west past the Florida Keys. I’d fetch it myself, but this hammock isn’t going to lie in itself.', do: 'hint:s2', options: [{label: 'Thanks, Mildew.', next: 'start'}]},
      again: {text: 'Dry Tortugas. West. Past the Keys. Shh.', options: [{label: 'Shh. Right.', next: 'start'}]},
      name: {text: 'I have been in this hammock a long time, Captain. A long, long time.', options: [{label: 'Fair enough.', next: 'start'}]}
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
      three: {text: 'All three! Then you know where to go: Smoke Cay, out in the open sea north of the Main. Follow the haze. The Emerald Bale is yours if you can dig it up.', options: [{label: 'I’m on my way.', next: 'start'}]},
      won: {text: 'Ha! Then you’re a Legend of the Reefer now. Try not to let it go to your head. It went to mine for about forty years.', options: [{label: 'I’ll try.', next: 'start'}]}
    }
  };

  /* Delivery requests: who asks, what for, and the reward. */
  var QUESTS = {
    percival:  {by: 'percival', port: 'portroyal', good: 'haze', n: 5, gold: 300},
    toussaint: {by: 'toussaint', port: 'petitgoave', good: 'mermaid', n: 2, gold: 350},
    catalina:  {by: 'catalina', port: 'havana', good: 'tangerine', n: 10, gold: 400},
    quill:     {by: 'quill', port: 'cartagena', good: 'kraken', n: 1, gold: 600},
    prudence:  {by: 'prudence', port: 'portobelo', good: 'cloud', n: 8, gold: 500}
  };

  var UPGRADES = {
    hold:     {name: 'Bigger hold', icon: '📦', levels: [20, 35, 60, 100], cost: [400, 1200, 3000], note: 'Room for more bales.'},
    sails:    {name: 'Faster sails', icon: '⛵', levels: [0, 1, 2], cost: [500, 1500], note: 'Sail faster and outrun Customs more often.'},
    cannons:  {name: 'More cannons', icon: '💣', levels: [0, 1, 2, 3], cost: [300, 900, 2000], note: 'Better odds when you board a merchant or fire a warning shot.'},
    lavender: {name: 'Lavender-lined hold', icon: '🌸', levels: [0, 1], cost: [800], note: 'Customs can’t smell your cargo from as far away.'}
  };

  var RANKS = [[0, 'Deckhand'], [600, 'Bosun'], [2000, 'Quartermaster'], [5000, 'Captain'], [12000, 'Commodore']];

  var CUSTOMS_NAMES = ['Lieutenant Dudley Clipboard', 'Ensign Agatha Stamp', 'Sergeant Percy Paperwork', 'Lieutenant Mabel Inkwell', 'Ensign Rupert Triplicate'];
  var MERCHANT_NAMES = ['the Prosperous Penny', 'the Comfortable Shoe', 'the Sensible Investment', 'the Mild Surprise', 'the Quarterly Report', 'the Reasonable Doubt', 'the Polite Cough'];

  /* Notes in bottles when no joke is to hand. */
  var BOTTLE_TIPS = [
    'The note reads: “Prices change every day. If a port won’t pay what you want, try again tomorrow, or try the next sea over.”',
    'The note reads: “Goods from another sea fetch the best prices. Tortuga Tangerine in Cartagena? Chef’s kiss.”',
    'The note reads: “Merchant ships carry Kraken Kush. Customs cutters carry clipboards. Choose your fights.”',
    'The note reads: “Whoever finds this: the haze over Smoke Cay never lifts. Signed, someone who got lost there for a week.”'
  ];

  var PARROT = 'Admiral Biscuit';

  window.PILLAGE_DATA = {GOODS: GOODS, COMMON: COMMON, MAPS: MAPS, PORTS: PORTS, STASHES: STASHES, PEOPLE: PEOPLE,
    QUESTS: QUESTS, UPGRADES: UPGRADES, RANKS: RANKS, CUSTOMS_NAMES: CUSTOMS_NAMES, MERCHANT_NAMES: MERCHANT_NAMES,
    BOTTLE_TIPS: BOTTLE_TIPS, PARROT: PARROT};
})();
