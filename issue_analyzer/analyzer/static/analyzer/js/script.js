$(document).ready(function(){
	'use strict';

	var path = location.protocol + '//' + location.host + location.pathname;

	var $loader = $('.loader');
	var $resultSec = $('.result-section');
	var $results = $('.results');
	var $noResults = $('.no-results');

	$('#searchForm').submit(function(e){
		e.preventDefault();
		
		$loader.removeClass('hidden');
		$resultSec.addClass('hidden');
		$noResults.addClass('hidden');
		$results.empty();

		var $this = $(this);
		var $query = encodeURIComponent($this.find('input[type=search]').val());
		var $level = 4 - parseInt($this.find('input[type=range]').val());
		var url = path + 'results?q=' + $query + '&level=' + $level;
		window.history.pushState({}, '', url.replace('results', ''));

		ajax(url, function(res){
			$loader.addClass('hidden');
			$resultSec.removeClass('hidden');

			$resultSec.find('.query').text('"' + res.q + '"');

			if(res.has_results){
				var solutions = res.results.solutions;
				var issues = res.results.similar;

				// Solution suggestions
				if(solutions.length > 0){
					for(var i = 0; i < solutions.length; i++){
						var sol = solutions[i];
						
						var $solPanel = $('<div/>', { class: 'panel panel-default'});
						var $panel = $('<div/>', { class: 'panel-body'});
						var $body = $('<p/>', { text: sol.body});
						var $solUrl = $('<p/>', { class: 'comment-link'});
						var $linkTxt = $('<span/>', {text: 'View in context: '});
						var $solLink = $('<a/>', { href: sol.html_url, text: sol.html_url, target:'_blank'});
						var $footer = $('<div/>', { class: 'panel-footer suggestion-score text-success'});
						var $i = $('<i/>', { class: 'fa fa-thumbs-up'});
						var $score = $('<span/>', { text: sol.positive_score });

						$solUrl.append([$linkTxt, $solLink]);
						$panel.append([$body, $solUrl]);
						$footer.append([$i, $score]);
						$solPanel.append([$panel, $footer]);
						$results.append($solPanel);
					}
				}

				if(solutions.length > 0 && issues.length > 0){
					var $divider = $('<hr/>', { class: 'result-divider'});

					$results.append($divider);
				}

				// Similar issues
				if(issues.length > 0){
					var $simPanel = $('<div/>', { class: 'panel panel-default similar-issues'});
					var $simHeading = $('<div/>', { class: 'panel-heading'});
					var $headerTitle = $('<h3/>', { text: 'Issues that may be similar to yours:', class:'panel-title'});
					var $simUl = $('<ul/>', { class: 'list-group'});

					$simHeading.append($headerTitle);
					$simPanel.append($simHeading);

					for(var j = 0; j < issues.length; j++){
						var issue = issues[j];

						var $simLi = $('<li/>', { class: 'list-group-item'});
						var $title = $('<p/>', { text: issue.title});
						var $simUrl = $('<p/>');
						var $simLink = $('<a/>', { href: issue.html_url, text: issue.html_url, target:'_blank'});

						$simUrl.append($simLink);
						$simLi.append([$title, $simUrl]);
						$simUl.append($simLi);
					}

					$simPanel.append($simUl);
					$results.append($simPanel);
				}

				$resultSec.removeClass('hidden');
			}else{
				$noResults.removeClass('hidden');
			}
		});
	});

}); // END ready

// Send an AJAX request
function ajax(url, callback, options){
	// Defaults
	var method = 'GET';
	var data = {};

	if(options !== undefined){
		method = options.method || method;
		data = options.data || data;
	}

	$.ajax({
		url: url,
		method: method,
		data: data,
		dataType: 'json'
	}).done(callback);
}