$(document).ready(function() {
	'use strict';

	function starPaste() {
		var paste_id = this.dataset.pasteId,
			url = this.dataset.url,
			data = {'paste': paste_id};

		$.post(url, data, starSuccess);
	}

	function starSuccess() {
		$('.star__action').addClass('is-disabled');
		$('.star__action .star__status').html('Starred');
		$('.star__action .fa').addClass('fa-star').removeClass('fa-star-o');
	}

	$('.star__action').click(starPaste);

	function addFileInputs() {
		/* Copy the filename and textarea inputs for a new file. */
		var $old_group = $('.paste-form__file-group').last(),
			$new_group = $old_group.clone();

		$new_group.find('.paste-form__filename').val('');
		$new_group.find('.paste-form__content').val('');
		$new_group.insertAfter($old_group);

		return $new_group;
	}

	$('.paste-form__add-file').click(addFileInputs);

	$('.notification').on('click', '.delete', function() {
		$(this).parent('.notification').remove();
	});


	function fileUploadSupported() {
		/* True if we want to support drag-n-drop file uploads. */
		return true;
	}

	$(document).on('dragenter dragover', '.paste-form__file-group', function() {
		$('input, textarea', this).addClass('drag-start');

		return false;
	});

	$(document).on('dragleave dragend dragexit drop', '.paste-form__file-group', function() {
		$('input, textarea', this).removeClass('drag-start');

		return false;
	});

	$(document).on('drop', '.paste-form__file-group', function(evt) {
		var files = evt.originalEvent.dataTransfer.files,
			dropTarget = this;

		$.each(files, function(idx, obj) {
			$('.paste-form__filename', dropTarget).val(obj.name);

			var reader = new FileReader();
			reader.onload = function(e) {
				$('.paste-form__content', dropTarget).val(e.target.result);
			};
			reader.readAsText(obj);
		});
	});
});
