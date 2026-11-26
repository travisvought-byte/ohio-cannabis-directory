/* Pillage the Reefer: little choose-your-own-adventure moments, at sea and in port.
   Each one gets a helper object (a) from the game: a.gold(), a.xp(), a.hurt(), a.give() and friends.
   A choice that shows its odds with a.odds(p) must roll them with a.check(p), so the number shown is the number rolled.
   Every choice returns the text that happens next. Losses stay small, so a bad roll never ruins a voyage. */
(function () {
  'use strict';

  var SEA = [
    {id: 'raft', title: '🛶 A castaway on a raft',
      text: 'A sunburnt sailor on a raft made of rum barrels waves both arms at you. He has the look of a man who has been talking to a coconut.',
      opts: function (a) {
        return [
          {label: 'Haul him aboard', fn: function () {
            if (a.chance(0.55)) {
              var map = a.giveMap();
              if (map) return 'He’s so grateful he cries a little, then presses a soggy scrap of paper into your hand. ' + map + a.xp(15);
              return 'He turns out to be a ship’s carpenter, and patches your hull before hopping off at the next port. ' + a.heal(12) + a.xp(15);
            }
            var lost = a.loseRandom(1);
            return 'He eats every biscuit aboard' + (lost ? ', plus ' + lost : '') + ', then waves goodbye at the next port. ' + a.parrot + ' will never forgive him.' + a.xp(10);
          }},
          {label: 'Toss him a coconut and sail on', fn: function () { return 'He catches it with both hands and gives you a thumbs-up. Then he starts talking to it.'; }}
        ];
      }},
    {id: 'wreck', title: '⚓ A drifting wreck',
      text: 'A half-sunk wreck rolls in the swell. Her hold is still above water, and something in there smells interesting.',
      opts: function (a) {
        return [
          {label: 'Search her hold (' + a.odds(0.7) + ')', fn: function () {
            if (a.check(0.7)) {
              var g = a.gold(a.rand(30, 70) * a.tier), got = a.giveRandom(a.rand(1, 3));
              return 'Behind a barrel of very old pickles you find ' + a.money(g) + (got ? ' and ' + got : '') + '.' + a.xp(10 + 5 * a.tier);
            }
            return 'A very large eel lives here now, and it has opinions. You leave fast, minus some paint. ' + a.hurtText(4 + 2 * a.tier);
          }},
          {label: 'Leave her in peace', fn: function () { return 'You tip your hat to the old girl and sail on.'; }}
        ];
      }},
    {id: 'whale', title: '🐋 A whale surfaces',
      text: 'A huge grey whale rises beside your ship, blows a rainbow out of the top of her head and looks you right in the eye.',
      opts: function (a) {
        return [
          {label: 'Follow her (' + a.odds(0.55) + ')', fn: function () {
            if (a.check(0.55)) {
              var n = a.give('mermaid', 2);
              return n ? 'She leads you to a patch of floating crates: ' + a.bales(n, 'mermaid') + '. She winks. Probably.' + a.xp(15)
                : 'She leads you to a patch of floating crates, but your hold is full. You wave them goodbye.' + a.xp(10);
            }
            return 'She dives deep and doesn’t come back. You’re a little further from anywhere, but it was nice while it lasted.' + a.xp(5);
          }},
          {label: 'Wave at her', fn: function () { return 'She waves back with a fin the size of a door. Your crew talks about it for days.' + a.xp(10); }}
        ];
      }},
    {id: 'squall', title: '⛈️ A squall rolls in',
      text: 'Black clouds pile up fast. The wind starts to howl, and ' + 'the parrot hides in your hat.',
      opts: function (a) {
        var sing = 0.45 + 0.08 * a.st.charm;
        return [
          {label: 'Ride it out', fn: function () { return 'You lash yourself to the wheel and come out the other side soaked, proud and slightly dented. ' + a.hurtText(a.rand(3, 7)) + a.xp(20); }},
          {label: 'Sing shanties until it passes (' + a.odds(sing) + ')', fn: function () {
            if (a.check(sing)) return 'Your crew sings so loudly and so badly that the storm gives up and goes somewhere else.' + a.xp(25);
            return 'The storm does not care for your singing. ' + a.hurtText(5) + a.xp(5);
          }},
          {label: 'Wait for it to blow over', fn: function () { return 'It takes an hour. Nothing happens, apart from a great deal of rain.'; }}
        ];
      }},
    {id: 'song', title: '🎶 Singing on the rocks',
      text: 'Lovely singing drifts across the water from a ring of rocks. Your crew gets a dreamy, faraway look.',
      opts: function (a) {
        return [
          {label: 'Steer toward the song (' + a.odds(0.5) + ')', fn: function () {
            if (a.check(0.5)) {
              var n = a.give('mermaid', 2);
              return 'Three cheerful mermaids are holding a bake sale. ' + (n ? 'You leave with ' + a.bales(n, 'mermaid') + ' and a recipe.' : 'Your hold is full, so you just buy a scone.') + a.xp(15);
            }
            return 'It’s rocks. Just rocks, and an echo, and now a scrape down your side. ' + a.hurtText(4 + a.tier * 2);
          }},
          {label: 'Stuff wax in everyone’s ears', fn: function () { return 'Nobody hears anything for the rest of the day, including your orders. Still, no rocks.'; }}
        ];
      }},
    {id: 'ghost', title: '👻 A ship in the fog', minTier: 2,
      text: 'A grey ship with ragged sails slides out of the fog. Nobody stands at her wheel. A lantern swings on its own.',
      opts: function (a) {
        return [
          {label: 'Board her (' + a.odds(0.5) + ')', fn: function () {
            if (a.check(0.5)) {
              var g = a.gold(a.rand(80, 160) * a.tier);
              return 'The “ghosts” are just very pale accountants who got lost doing an audit. They’re so relieved to see anyone that they give you ' + a.money(g) + '.' + a.xp(30);
            }
            var lost = a.loseRandom(2);
            return 'Something below decks says “BOO.” Your entire crew jumps overboard, then climbs back aboard, wet and embarrassed.' + (lost ? ' Somebody dropped ' + lost + ' in the panic.' : '') + a.xp(5);
          }},
          {label: 'Salute and sail on', fn: function () { return 'The lantern dips, as if in thanks. You decide not to think about it.' + a.xp(5); }}
        ];
      }},
    {id: 'crab', title: '🦀 A very large crab',
      text: 'A crab the size of a rowing boat has grabbed your anchor chain and won’t let go. It looks hungry and a bit smug.',
      opts: function (a) {
        var win = Math.min(0.9, 0.4 + 0.08 * a.st.fight + 0.05 * a.st.cannons);
        var out = [
          {label: 'Fight it (' + a.odds(win) + ')', fn: function () {
            if (a.check(win)) return 'After a long and undignified struggle, the crab lets go. Your cook makes a crab stew that patches everyone up. ' + a.heal(10) + a.xp(25);
            return 'The crab wins. It takes a bite out of your rail and lets go when it gets bored. ' + a.hurtText(6) + a.xp(5);
          }},
          {label: 'Wait it out', fn: function () { return 'Two hours later it lets go and wanders off sideways, as crabs do.'; }}
        ];
        if (a.cargo() > 0) out.splice(1, 0, {label: 'Offer it a bale', fn: function () { var lost = a.loseRandom(1); return 'It takes ' + lost + ', lets go and scuttles off, delighted.' + a.xp(10); }});
        return out;
      }},
    {id: 'party', title: '🎉 A party barge',
      text: 'A barge full of merchants in paper hats drifts past. Somebody is playing a very small accordion. They wave you over.',
      opts: function (a) {
        var out = [];
        if (a.cargo() > 0) out.push({label: 'Sell them a few bales at party prices', fn: function () { return a.sellRandom(3, 1.5, 'The partygoers are thrilled.'); }});
        out.push({label: 'Join the party (30 doubloons)', disabled: !a.hasGold(30), fn: function () {
          a.gold(-30);
          var map = a.chance(0.5) ? a.giveMap() : null;
          return 'You dance, you sing, you lose a boot.' + (map ? ' Somebody’s uncle tells you a secret. ' + map : ' Nobody tells you any secrets, but it was a good night.') + a.xp(20);
        }});
        out.push({label: 'Wave and keep going', fn: function () { return 'They cheer as you sail past. The accordion player does not stop.'; }});
        return out;
      }},
    {id: 'turtle', title: '🐢 A tangled turtle',
      text: 'An old sea turtle is caught in a fishing net, flapping slowly and looking at you with enormous, patient eyes.',
      opts: function (a) {
        return [
          {label: 'Cut it free', fn: function () {
            var n = a.chance(0.35) ? a.give('mermaid', 1) : 0;
            return 'You cut the net away. The turtle swims a slow circle around your ship to say thanks' + (n ? ', then nudges a floating bale of Mermaid’s Kiss your way.' : '.') + a.xp(20);
          }},
          {label: 'Sail on', fn: function () { return 'You sail on. ' + a.parrot + ' gives you a long, disappointed look.'; }}
        ];
      }},
    {id: 'mapmaker', title: '🗺️ A mapmaker in a rowboat', needsNoMap: true,
      text: 'A man in a rowboat and an enormous hat holds up a rolled map. “Treasure! Genuine! Mostly!”',
      opts: function (a) {
        var cost = 60 + 50 * a.tier;
        return [
          {label: 'Buy the map for ' + cost + ' doubloons', disabled: !a.hasGold(cost), fn: function () { a.gold(-cost); return 'He takes the coins, bows so low his hat falls in the sea, and rows off. ' + a.giveMap(); }},
          {label: 'No thanks', fn: function () { return '“Your loss!” he shouts, and rows away to find someone more gullible.'; }}
        ];
      }},
    {id: 'race', title: '🏁 A rival wants to race',
      text: 'A rival sloop pulls alongside. Her captain grins. “Race you to that rock! Loser buys the rum.”',
      opts: function (a) {
        var p = Math.min(0.9, 0.4 + 0.08 * a.st.sails + 0.05 * a.st.sail);
        return [
          {label: 'Race! (' + a.odds(p) + ')', fn: function () {
            if (a.check(p)) { var g = a.gold(40 * a.tier); return 'You round the rock a full length ahead. Your rival pays up with good grace: ' + a.money(g) + '.' + a.xp(20); }
            var lost = -a.gold(-Math.min(a.goldNow(), 20 * a.tier));
            return 'You lose by a nose, and a bit of pride.' + (lost ? ' The rum costs you ' + a.money(lost) + '.' : '') + a.xp(5);
          }},
          {label: 'Decline politely', fn: function () { return '“Chicken!” she shouts. ' + a.parrot + ' takes this personally.'; }}
        ];
      }},
    {id: 'smoke', title: '🔥 Smoke from a hidden cove', needsNoMap: true,
      text: 'A thin, sweet-smelling smoke curls up from a cove. Someone was camping here, and left in a hurry.',
      opts: function (a) {
        return [
          {label: 'Row ashore and look around', fn: function () { return 'Half-buried in the warm ashes you find a scorched treasure map. ' + a.giveMap() + a.xp(10); }},
          {label: 'Not our business', fn: function () { return 'You leave the cove alone. Somewhere ashore, someone sighs with relief.'; }}
        ];
      }},
    {id: 'tentacles', title: '🐙 Tentacles!', minTier: 3,
      text: 'Huge purple tentacles rise out of the sea all around your ship. They seem more curious than cross. For now.',
      opts: function (a) {
        var p = Math.min(0.9, 0.35 + 0.1 * a.st.cannons + 0.04 * a.st.fight);
        var out = [{label: 'Fire the cannons (' + a.odds(p) + ')', fn: function () {
          if (a.check(p)) { var n = a.give('kraken', 1); return 'BOOM. The tentacles slither off in a huff' + (n ? ', and something drifts up in their wake: a bale of Kraken Kush.' : '.') + a.xp(40); }
          return 'BOOM. You miss. A tentacle gives your mast a firm squeeze before it lets go. ' + a.hurtText(10) + a.xp(10);
        }}];
        if (a.cargo() > 0) out.push({label: 'Offer it a bale', fn: function () { var lost = a.loseRandom(1); return 'A tentacle takes ' + lost + ', very gently, and gives your ship a friendly pat goodbye.' + a.xp(15); }});
        out.push({label: 'Sit very still (' + a.odds(0.6) + ')', fn: function () {
          if (a.check(0.6)) return 'You all hold your breath. After a while the tentacles lose interest and sink away.' + a.xp(10);
          return 'You sit very still. A tentacle pokes you anyway, quite hard. ' + a.hurtText(5);
        }});
        return out;
      }}
  ];

  var PORT = [
    {id: 'carnival', title: '🎉 Carnival in town!',
      text: 'The whole port is dancing. Drums, feathers, fried plantains and a goat in a hat.',
      opts: function (a) {
        var out = [{label: 'Dance!', fn: function () { return 'You dance until your boots fall apart. Everyone in town now knows your name.' + a.xp(20); }}];
        if (a.cargo() > 0) out.push({label: 'Sell to the crowd', fn: function () { return a.sellRandom(4, 1.4, 'The crowd snaps them up.'); }});
        out.push({label: 'Head straight for the docks', fn: function () { return 'You squeeze through the crowd and get down to business.'; }});
        return out;
      }},
    {id: 'armwrestle', title: '💪 An arm-wrestling challenge',
      text: 'A dock worker with forearms like hams slams an elbow on a barrel. “Beat me and dinner’s on me. Lose and you’re buying.”',
      opts: function (a) {
        var p = Math.min(0.9, 0.35 + 0.1 * a.st.fight);
        return [
          {label: 'Accept (' + a.odds(p) + ')', fn: function () {
            if (a.check(p)) { var g = a.gold(30 * a.tier); return 'You win with a mighty grunt. The whole dock cheers, and your new friend pays for dinner and ' + a.money(g) + ' on top.' + a.xp(15); }
            var lost = -a.gold(-Math.min(a.goldNow(), 10 * a.tier));
            return 'Your arm goes flat on the barrel so fast it makes a noise.' + (lost ? ' Dinner costs you ' + a.money(lost) + '.' : '') + a.xp(5);
          }},
          {label: 'Not today', fn: function () { return '“Suit yourself,” they say, and turn to the next sailor.'; }}
        ];
      }},
    {id: 'shadymap', title: '🗺️ A shady mapmaker', needsNoMap: true,
      text: 'A woman in a long coat sidles up. “Psst. Treasure map. Real one. I just don’t like digging.”',
      opts: function (a) {
        var cost = 50 + 50 * a.tier;
        return [
          {label: 'Buy it for ' + cost + ' doubloons', disabled: !a.hasGold(cost), fn: function () { a.gold(-cost); return 'She counts the coins twice, hands you the map and vanishes into the crowd. ' + a.giveMap(); }},
          {label: 'No thanks', fn: function () { return 'She shrugs and sidles off to sidle up to someone else.'; }}
        ];
      }},
    {id: 'pickpocket', title: '🧤 A pickpocket!',
      text: 'You feel a light tug at your belt. A small boy in a very large hat is strolling away with your purse, extremely casually.',
      opts: function (a) {
        var p = Math.min(0.9, 0.55 + 0.06 * a.st.sail);
        return [
          {label: 'Chase him down (' + a.odds(p) + ')', fn: function () {
            if (a.check(p)) {
              var map = a.chance(0.5) ? a.giveMap() : null;
              if (map) return 'You catch him by the hat. He hands back your purse and, impressed, sells you a secret for nothing. ' + map + a.xp(15);
              var g = a.gold(25 * a.tier);
              return 'You catch him by the hat. He hands back your purse, plus ' + a.money(g) + ' he lifted from somebody else.' + a.xp(15);
            }
            var lost = -a.gold(-Math.min(a.goldNow(), 15 * a.tier));
            return 'He’s gone around a corner, over a wall and into a cart of melons. ' + (lost ? 'Your purse is lighter by ' + a.money(lost) + '.' : 'Luckily it was empty.');
          }},
          {label: 'Shout “Oi!”', fn: function () { return 'He drops the purse and runs. Nothing’s missing except your dignity.'; }}
        ];
      }},
    {id: 'oldsalt', title: '🧓 An old sea dog', once: true,
      text: 'An old sailor with one boot and a thousand stories offers to teach you a trick or two, for the price of a proper dinner.',
      opts: function (a) {
        return [
          {label: 'Buy him dinner (150 doubloons)', disabled: !a.hasGold(150), fn: function () { a.gold(-150); return 'Over three helpings of stew he shows you how a real captain does it. ' + a.skillPoint(); }},
          {label: 'Maybe another night', fn: function () { return '“Your loss, young’un,” he says, and orders more stew anyway.'; }}
        ];
      }},
    {id: 'carpenter', title: '🔨 A grateful carpenter', needsDamage: true,
      text: 'A carpenter on the dock looks at your battered hull and tuts. “I owe your parrot a favour. Don’t ask.”',
      opts: function (a) {
        return [{label: 'Accept gratefully', fn: function () { return 'Two hours of hammering later, your ship looks much happier. ' + a.heal(20) + a.xp(5); }}];
      }},
    {id: 'auction', title: '📣 A dockside auction',
      text: 'The harbourmaster is auctioning off cargo that some smugglers forgot to collect. Nobody else is bidding.',
      opts: function (a) {
        var n = Math.min(a.space(), a.rand(4, 6)), cost = n * 18 * a.tier;
        var out = [];
        if (n > 0) out.push({label: 'Bid on ' + n + ' mystery bales (' + cost + ' doubloons)', disabled: !a.hasGold(cost), fn: function () {
          a.gold(-cost);
          return 'Sold, to the captain with the parrot! You get ' + a.giveRandom(n) + '.';
        }});
        out.push({label: 'Just watch', fn: function () { return 'You watch a man buy a crate of left boots. Nobody knows why.'; }});
        return out;
      }}
  ];

  window.PILLAGE_EVENTS = {sea: SEA, port: PORT};
})();
