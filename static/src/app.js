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

	function add_file_inputs() {
		/* Copy the filename and textarea inputs for a new file. */
		var $old_group = $('.paste-form__file-group').last(),
			$new_group = $old_group.clone();

		$new_group.find('.paste-form__filename').val('');
		$new_group.find('.paste-form__content').val('');
		$new_group.insertAfter($old_group);
	}

	$('.paste-form__add-file').click(add_file_inputs);

	$('.notification').on('click', '.delete', function() {
		$(this).parent('.notification').remove();
	});
});
