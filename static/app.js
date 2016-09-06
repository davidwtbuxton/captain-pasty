$(document).ready(function() {
	'use strict';

	function star_paste() {
		var paste_id = this.dataset.pasteId;
		console.log('paste', paste_id);
	}

	$('.star__action').click(star_paste);
});
