$(document).ready(function() {
	'use strict';


	/* Starring and un-starring pastes. */
	function starPaste() {
		var pasteId = this.dataset.pasteId,
			urlCreate = this.dataset.urlCreate,
			urlDelete = this.dataset.urlDelete,
			data = {'paste': pasteId},
			url,
			isStarred;

		isStarred = $('.star__status', this).html() === 'Starred';
		url = isStarred ? urlDelete: urlCreate;

		$.post({
			url: url,
			data: data,
			headers: {'X-CSRFToken': this.dataset.csrfToken},
			success: function() {
				if (isStarred) {
					$('.star__action .star__status').html('Star');
					$('.star__action .fa').addClass('fa-star-o').removeClass('fa-star');
				} else {
					$('.star__action .star__status').html('Starred');
					$('.star__action .fa').addClass('fa-star').removeClass('fa-star-o');
				}
			}
		});
	}

	$('.star__action').click(starPaste);


	/* The "add file" button on the new paste form. */
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


	/* Dismiss notifications (admins). */
	$('.notification').on('click', '.delete', function() {
		$(this).parent('.notification').remove();
	});


	/* Drag-and-drop files into the new paste form. */
	$('.paste-form')
		.on('dragenter dragover', '.paste-form__file-group', function() {
			$('input, textarea', this).addClass('drag-start');

			return false;
		})
		.on('dragleave dragend dragexit drop', '.paste-form__file-group', function() {
			$('input, textarea', this).removeClass('drag-start');

			return false;
		})
		.on('drop', '.paste-form__file-group', function(evt) {
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


	/* Show / hide the advanced search form. */
	function hideAdvancedSearch(evt) {
		if (! $(evt.target).parents('.search').length) {
			$('.advanced-search').addClass('hidden');
			$(document).off('click', hideAdvancedSearch);
		}
	}

	function showAdvancedSearch() {
		$('.advanced-search').removeClass('hidden');
		// Make sure we don't bind it more than once.
		$(document).off('click', hideAdvancedSearch);
		$(document).on('click', hideAdvancedSearch);
	}

	// $('.search').on('focus', 'input', showAdvancedSearch);
});
