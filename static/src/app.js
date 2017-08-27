$(document).ready(function() {
	'use strict';

	/* Copied from https://davidwalsh.name/javascript-debounce-function */
	function debounce(func, wait, immediate) {
		var timeout;

		return function() {
			var context = this, args = arguments;
			var later = function() {
				timeout = null;
				if (!immediate) func.apply(context, args);
			};
			var callNow = immediate && !timeout;
			clearTimeout(timeout);
			timeout = setTimeout(later, wait);
			if (callNow) func.apply(context, args);
		};
	}


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

				updateStarListDebounced();
			}
		});
	}

	function buildStarItem(obj, idx) {
		var markup = '<li class="stars__summary"><a href="{{ url }}">{{ author }} / {{ filename }}</a></li>';
		markup = markup
			.replace('{{ url }}', obj.url)
			.replace('{{ author }}', obj.author || 'anonymous')
			.replace('{{ filename }}', obj.filename);

		return $(markup);
	}


	function updateStarList() {
		var $listEl = $('.stars__list'),
			urlList = $listEl.get(0).dataset.urlList;

		$.get({
			url: urlList,
			success: function(data) {
				var itemElements = $.map(data.stars, buildStarItem);
				$listEl.empty().append(itemElements);
			}
		});
	}


	var updateStarListDebounced = debounce(updateStarList, 250);


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

});
