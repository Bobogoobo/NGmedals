//Newgrounds Medals Quick View by Bobogoobo, copyright 2022
//Run on https://www.newgrounds.com/gameswithmedals/
//	Copy the entire file, open the browser console (F12), and paste.
//	Needs to be re-run on each page.
//	Delays each request by one second for NG rate limits.
//	Check near first line of code for configuration options.
//Note: unearned secret medals will skew points completion values.
//Please report any bugs, suggestions, questions, etc by PM ( https://bobogoobo.newgrounds.com/ )
//TODO: formatting doesn't work in Chrome console; save whole thing in a string for the end
//todo: there's also the `medals` variable that has everything, not sure if I can access that, might have to parse from page code.

//Color coding:
//	faded = 100%
//	green = 75% to 100%
//	yellow = 50% to 75%
//	red = 25% to 50%
//	blue = 0% to 25%
//	no color = unstarted

;(function() {
	var debug = false;// change to true to run only on first five games listed
	var completionByMedals = true;// change to false to evaluate completion highlighting by points

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
		var completion = 0, background = [], opacity = 25;
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
		console.log(
			'%s (%s): %.3d / %.3d medals [%s%], %.4d / %.4d points [%s%]%s',
			gameData.title.padStart(100, ' '),
			gameData.id.padStart(7, ' '),
			gameData.medalsEarned,
			gameData.medalsTotal,
			(Math.round(gameData.medalsEarned / gameData.medalsTotal * 100) || 0).toString().padStart(3, ' '),
			gameData.pointsEarned,
			gameData.pointsTotal,
			(Math.round(gameData.pointsEarned / gameData.pointsTotal * 100) || 0).toString().padStart(3, ' '),
			gameData.unearnedSecret ? '* (' + gameData.unearnedSecret + ' secret)' : ''
		);
		//Determine styling
		if (completion === 100) {
			opacity = 20;
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
		
	}

	document.querySelectorAll('.podcontent .game > a').forEach(function(gameLink, i) {
		if (!debug || (debug && i < 5)) {
			setTimeout(getPage, 1000 * i, gameLink, parsePage);
		}
	});
})();