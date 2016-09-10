$(document).ready(function() {
	'use strict';

	function star_paste() {
		var paste_id = this.dataset.pasteId,
			url = this.dataset.url,
			data = {'paste': paste_id};

		$.post(url, data, star_success);
	}

	function star_success() {
		$('.star__action').addClass('is-disabled');
		$('.star__action .star__status').html('Starred');
		$('.star__action .fa').addClass('fa-star').removeClass('fa-star-o');
	}

	$('.star__action').click(star_paste);
});
