//Newgrounds Medals Quick View by Bobogoobo, copyright 2022
//Shows your medal progress in each game at a glance on the Games With Medals collection page.
//Run on https://www.newgrounds.com/gameswithmedals/
//	Copy the entire file, open the browser console (F12), paste, and press Enter.
//	Needs to be re-run on each page.
//		(After the first time, you should be able to just press the up arrow in the console and then press Enter.)
//	Delays each request by one second for NG rate limits.
//	Check near first line of code for configuration options.
//Note: unearned secret medals will skew points completion values.
//Please report any bugs, suggestions, questions, etc by PM ( https://bobogoobo.newgrounds.com/ )
//TODO: something if all non-secret medals are broken
//TODO: indication of running for when a lot are unplayed
//TODO: on someone else's medals page have to open the compare link and parse that instead
//	on author page would take multiple steps but compare link works even if they haven't played it, just need the game's medals api id
//todo: something on your own medals page
//todo: better styling (more intuitive)
//todo: on game pages there's also the `medals` variable that has everything, not sure if I can access that, might have to parse from page code.

//Color coding (open to suggestions):
//	very faded = broken
//	faded = 100%
//	green = 75% to 100%
//	yellow = 50% to 75%
//	red = 25% to 50%
//	blue = 0% to 25%
//	no color = unstarted

;(function() {
	var debug = false;// change to true to run only on first five games listed
	var completionByMedals = true;// change to false to evaluate completion highlighting by points

	var mode;
	var finalOut = '';
	var pending = 0;

	function pad(num, len, str) {
		return num.toString().padStart(len || 3, str || ' ');
	}

	function getPage(gameLink, callback, isRetry) {
		var url = gameLink.getAttribute('href');
		var title = gameLink.querySelector('img').getAttribute('alt');

		var req = new XMLHttpRequest();
		req.onreadystatechange = function() {
			var page, toRetry = false, errorText = '';

			if (req.readyState !== XMLHttpRequest.DONE) {
				return;
			}
			if (req.status === 200) {
				try {
					page = document.createElement('div');
					jQuery(page).append(jQuery.parseHTML(req.responseText));
				} catch (err) {
					toRetry = true;
					errorText = err.toString();
				}
			} else {
				toRetry = true;
				errorText = req.status + ' ' + req.statusText;
			}
			//Retry once after ten seconds
			if (toRetry) {
				if (isRetry) {
					console.log('Could not retrieve "' + title + '" (' + url.split('/').slice(-1)[0] + '): ' + errorText);
					return;
				}
				console.log('Failed to retrieve "' + title + '" (' + url.split('/').slice(-1)[0] + '). Retrying in ten seconds. ' + errorText);
				setTimeout(getPage, 10000, gameLink, callback, true);
			} else {
				callback(page, gameLink);
			}
		};
		req.open('GET', url);
		req.send();
	}

	function parsePage(page, elem) {
		if (debug) {
			console.log(page);
		}

		var output = '';
		var completion = 0, isBroken = false, background = [], opacity = 25;
		var gameData = {
			id: elem.getAttribute('href').split('/').slice(-1)[0],
			title: page.querySelector('#embed_header h2').textContent.trim(),
			medalsEarned: 0,
			medalsTotal: 0,
			pointsEarned: 0,
			pointsTotal: 0,
			unearnedSecret: 0,
		};

		//Collect medal data
		medals = page.querySelectorAll('.item-ngio-medal');
		medals.forEach(function(med) {
			var icon = med.querySelector('.medal-icon');
			var earned = icon.classList.contains('unlocked');
			var value = parseInt(page.querySelector('#hov-for-' + med.getAttribute('id')).querySelector('h4 span').textContent.replace(' Points', ''), 10);
			gameData.medalsEarned += +earned;
			gameData.medalsTotal += 1;
			gameData.pointsEarned += earned ? value : 0;
			gameData.pointsTotal += Number.isNaN(value) ? 0 : value;
			gameData.unearnedSecret += +icon.classList.contains('secret');
		});
		completion = Math.round((completionByMedals ? gameData.medalsEarned / gameData.medalsTotal : gameData.pointsEarned / gameData.pointsTotal) * 100);
		if (completion === 100 && gameData.unearnedSecret || Number.isNaN(completion)) {
			completion = 0;
		}
		if (!gameData.medalsTotal || (!gameData.unearnedSecret && !gameData.pointsTotal)) {
			isBroken = true;
		}

		//Add to console output
		output = [
			pad(gameData.title, 100),
			'(' + pad(gameData.id, 7) + '):',
			pad(gameData.medalsEarned),
			'/',
			pad(gameData.medalsTotal),
			'medals',
			'[' + pad(Math.round(gameData.medalsEarned / gameData.medalsTotal * 100) || 0) + '%]',
			'|',
			pad(gameData.pointsEarned, 4),
			'/',
			pad(gameData.pointsTotal, 4),
			'points',
			'[' + pad(Math.round(gameData.pointsEarned / gameData.pointsTotal * 100) || 0) + '%]',
		];
		if (gameData.unearnedSecret) {
			output[output.length - 1] += '*';
			output.push('(' + gameData.unearnedSecret + ' secret)');
		}
		if (isBroken) {
			output.push('(seems broken)');
		}
		if (finalOut) {
			finalOut += '\n';
		}
		finalOut += output.join(' ');

		//Determine styling
		if (isBroken) {
			opacity = 5;
		} else if (completion === 100) {
			opacity = 25;
		} else if (completion < 100 && completion >= 75) {
			background = [0, 128, 0];
		} else if (completion < 75 && completion >= 50) {
			background = [128, 128, 0];
		} else if (completion < 50 && completion >= 25) {
			background = [128, 0, 0];
		} else if (completion < 25 && completion > 0) {
			background = [0, 0, 128];
		} else {
			opacity = null;
		}
		if (background.length) {
			background.push(opacity >= 0 && opacity <= 100 ? opacity : 100);
			elem.parentElement.style.setProperty('background-color', 'rgba(' + background.join(',') + '%)', 'important');
		} else if (opacity >= 0 && opacity <= 100) {
			elem.parentElement.style.opacity = opacity + '%';
		}

		checkDone();
	}

	function checkDone() {
		pending -= 1;
		if (!pending) {
			console.log(finalOut);
		}
	}

	function start() {
		var selector;
		var href = window.location.href.replace(window.location.search, '').replace(/sort\/(?:date|title)\/page\/\d+/, '');
		var page = href.slice(href.indexOf('.'));

		if (debug) {
			console.log('Debug mode');
		}

		if (href === 'https://www.newgrounds.com/gameswithmedals/') {
			mode = 'gwm';
		} else if (page === '.newgrounds.com/games/' || page === '.newgrounds.com/movies/') {
			//Doesn't work due to being different domain or something
			mode = 'author';
		} else if (page === '.newgrounds.com/stats/medals') {
			if (document.querySelector('.user-link').textContent === document.querySelector('.usermenu-userlink')) {
				mode = 'mymedals';
			} else {
				mode = 'medalstats';
			}
		}

		selector = {
			'gwm': '.podcontent .game > a, .podcontent .movie > a',
			'author': '.portalsubmission-cell > a',
			'medalstats': '.medal-game-meta > div > a',
		}[mode];

		document.querySelectorAll(selector).forEach(function(gameLink, i) {
			if (!debug || (debug && i < 5)) {
				pending += 1;
				setTimeout(getPage, 1000 * i, gameLink, parsePage);
			}
		});
	}

	start();
})();