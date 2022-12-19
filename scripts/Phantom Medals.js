// Usage: copy all, open browser console (F12), paste, press enter, wait about 1 second per page of medals.
// Do not run more than one copy at a time due to NG request rate limiting.
// Newgrounds Episode I: The Phantom Medals
// Directed by Bobogoobo
// Written by NeonSpider and HerbieG
// Produced by Nijsse
// Casting by Tom Fulp
// Dedicated to PsychoGoldfish
// copyright Bobogoobo MMXIX
//todo: include username in output
(function() {
	var $ = jQuery;
	var results = [];
	var extraPoints = 0, minusPoints = 0;
	
	var numPages;
	var baseURL = window.location.href.split('?')[0];
	var donePages = 0;
	
	var findStats = /Medals Earned\: (\d+)\/(\d+)\(([\d,]+)\/([\d,]+) points\)/;
	var findId = /\/(\d+)$/;
	
	try {
		numPages = $('#medals_pagenav a span').last().text().replace(',', '');
	} catch(err) {
		console.log('Could not find page count.', err.message);
		return;
	}
	if (!numPages) {
		numPages = 1;
	}
	
	function checkDone() {
		var res;
		donePages += 1;
		if (donePages % 10 === 0) {
			console.log(donePages + ' pages done');
		}
		if (donePages == numPages) {
			if (results.length) {
				console.log('Found %d games with issues.', results.length);
				results.sort(function(a, b) {
					if (a.page[0] === b.page[0]) {
						return a.page[1] - b.page[1];
					}
					return a.page[0] - b.page[0];
				});
				console.log('Game Title | Game ID | Reason | Errors | Shown Earned Medals (Unlocked Medals) / Available Medals | Shown Earned Points (Unlocked Points) / Available Points | Page (#)');
				for (var r = 0; r < results.length; r++) {
					res = results[r];
					console.log(
						res.title + ' | ' + res.gameId + ' | ' + res.reason + ' | ' + res.errors + ' | ' +
						res.medals[0] + ' (' + res.medals[1] + ') / ' + res.medals[2] + ' | ' +
						res.points[0] + ' (' + res.points[1] + ') / ' + res.points[2] + ' | ' +
						res.page[0] + ' (' + res.page[1] + ')'
					);
				}
				console.log('Phantom Points: ' + extraPoints);
				console.log('Missing Points: ' + minusPoints);
			} else {
				console.log('No medal issues found.');
			}
		}
	}
	
	for (var i = 1; i <= numPages; i++) {
		setTimeout(function(pageNum) {
			$.ajax(baseURL + '?page=' + pageNum).fail(function(req, stat, error) {
				console.log(error + ' - page ' + pageNum);
			}).done(function(medPage) {
				$('.two3', medPage).slice(1, -1).each(function(j, game) {
					var gameInfo, earnMed, totMed, earnPoint, totPoint;
					var $medalInfo, realEarnMed = 0, realEarnPoint = 0;
					var title, gameId, reason;
					var fail = [];
					//var curPage = $('#medals_pagenav a:not([href]) span', medPage).last().text().replace(',', '');
					
					try {
						gameInfo = $('.podcontent .moreinfo', game).text().trim().replace(/\t|\n/g, '').match(findStats);
						earnMed = +gameInfo[1];
						totMed = +gameInfo[2];
						earnPoint = +(gameInfo[3].replace(',', ''));
						totPoint = +(gameInfo[4].replace(',', ''));
					} catch(err) {
						fail.push(err.message);
					}
					
					try {
						$medalInfo = $('.gamesupport-medals .medalstatus-unlocked', game);
						$medalInfo.each(function(k, medal) {
							realEarnMed += 1;
							realEarnPoint += +$(medal).next().find('em').html().split('<br>')[1].trim().replace(' Points', '');
						});
					} catch(err) {
						fail.push(err.message);
					}
					
					if (fail.length) {
						reason = 'Parsing failed';
					} else if (realEarnMed < earnMed || realEarnPoint < earnPoint) {
						reason = 'Medals/points more than unlocked (Extra)';
						extraPoints += earnPoint - realEarnPoint;
					} else if (realEarnMed > earnMed || realEarnPoint > earnPoint) {
						reason = 'Medals/points less than unlocked (Missing)';
						minusPoints += realEarnPoint - earnPoint;
					} else if (earnMed > totMed || earnPoint > totPoint) {
						reason = 'Earned medals/points greater than available number';
						extraPoints += earnPoint - totPoint;
					}
					
					try {
						title = $('.podtop .game', game).text().trim();
					} catch(err) {
						fail.push(err.message);
						title = 'unknown';
					}
					try {
						gameId = $('.podtop a', game).last().attr('href').match(findId)[1];
					} catch(err) {
						fail.push(err.message);
						gameId = '-1';
					}
					
					if (reason) {
						results.push({
							'title': title,
							'gameId': gameId,
							'reason': reason,
							'errors': fail.toString(),
							'medals': [earnMed, realEarnMed, totMed],
							'points': [earnPoint, realEarnPoint, totPoint],
							'page': [+pageNum, j+1],
						});
					}
				});
			}).always(checkDone);
		}, 1000 * i, i);
	}
}());