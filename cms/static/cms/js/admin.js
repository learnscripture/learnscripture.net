var cms_jQuery = $.noConflict(true);

// cms namespace
var Cms = {};

Cms.enhance_textarea = function(textarea) {};
Cms.remove_textarea = function(textarea) {};

(function($) { // start of jQuery noConflict mode

// some plugins use jQuery() instead of $()
jQuery = $;

// abstract class for a basic admin dialog
var AdminDialog = Class.extend({

	// default options
	defaults: {
		url: null,
		width: 764,
		height: 'auto',
		start_width: 764,
		start_height: 480
	},

	// constructor
	init: function(options) {
		this.options = $.extend({}, this.defaults, options); // TODO: get dialog dimensions and behavior from options
		this.create_dialog();
		this.init_dialog();
		this.open();
	},

	// create a basic dialog, use only as example
	create_dialog: function() {
		this.uiDialog = $(document.createElement('div')).dialog({
			autoOpen: false,
			modal: true,
			resizable: false,
			width: this.options.start_width,
			height: this.options.start_height,
			position: ['center', 40]
		});

		this.uiDialog.dialog('option', 'title', gettext('Action')); // TODO: dynamically fill in action

		this.uiDialog.dialog('option', 'buttons', {
			'Action': {
				text: 'Action', // TODO: dynamically fill in action
				click: $.proxy(function() {
					this.action_click();
				}, this)
			},
			'Cancel': {
				text: gettext('Cancel'),
				click: $.proxy(function() {
					this.cancel_click();
				}, this)
			}
		});

		this.uiDialog.dialog('option', 'close', $.proxy(this.close, this));
	},

	// initialize the dialog
	init_dialog: function() {},

	redraw: function() {
		this.uiDialog.dialog('option', 'width', this.options.width);
		this.uiDialog.dialog('option', 'height', this.options.height);
		this.uiDialog.dialog('option', 'position', ['center', 40]);
	},

	advanced_fieldset_behaviour: function() {
		var advancedFieldsets = this.admin_form.form.find('fieldset:not(fieldset:first-child)');
		if (advancedFieldsets.length > 0) {

			advancedFieldsets.each(function() {
				var fieldset = $(this),
					button   = $('<a>');

				fieldset
					.addClass('advanced-fieldset')
					.hide();

				button
					.attr('href', '#')
					.text(fieldset.find('h2').text())
					.addClass('ui-dialog-buttonpane advanced-button closed')
					.click(function(e) {
						e.preventDefault();
						$(this).toggleClass('closed')
						fieldset.slideToggle('fast');
					})
					.insertBefore(fieldset);

				$('<span>')
					.text('»')
					.addClass('toggler')
					.prependTo(button);

				fieldset.find('h2').remove();
			});
		}
	},

	cancel_click: function() {
		this.close();
	},

	// customize open dialog behavior
	open: function() {
		this.uiDialog.dialog('open');
		this.redraw();
	},

	// customize close dialog behavior
	close: function() {
		this.uiDialog.dialog('option', 'close', null); // prevent recursive calls to this function
		this.uiDialog.dialog('close');
	},

	// customize destroy dialog behavior
	destroy: function() {
		this.uiDialog.dialog('destroy');
	}
});


// abstract class for a basic admin REST dialog
var AdminRESTDialog = AdminDialog.extend({

	// initialize the REST call
	init_dialog: function() {
		$.ajax({
			url: this.options.url,
			context: this,
			success: function(data) {
				if (this.init_dialog_success) {
					this.init_dialog_success(data);
				}
			}
		});
	}
});


function enhance_textareas(container, auto_height) {
	container.find('textarea.cms-editor').each(function() {
		Cms.enhance_textarea(this, auto_height);
	});
}

var BaseFileSelectDialog = AdminRESTDialog.extend({

	open: function() {
		this._super();
		// Create the upload button after displaying the dialog
		this.create_upload_button();
		this.create_delete_button();
	},

	get_upload_path: function() {
		// override this
	},

	refresh_grid: function() {
		this.select_grid.simple_datagrid('reload');

		// very crude way of disabling the delete button when the grid (and thus the selection) changes
		var delete_button = $('#delete-buttonpane button');
		delete_button.attr('disabled', 'disabled');
		delete_button.addClass('ui-button-disabled ui-state-disabled');
	},

	get_upload_fieldname: function() {
		return 'file';
	},

	uneditables_formatter: function(value, row_data) {
		if (!row_data.can_edit) {
			return '<span class="non-editable">' + value + '</span>';
		}
			return value;
	},

	create_upload_button: function() {
		var button_pane = this.uiDialog.parent().find('.ui-dialog-buttonpane');

		var upload_button_pane = $('<div/>').prependTo(button_pane)
			.attr({
				'id': 'upload-buttonpane'
			});

		var upload_button = $('<a>' + gettext('Upload a new file') + '</a>')
			.appendTo(upload_button_pane)
			.attr({
				'class': 'upload',
				'id': 'upload-file-button'
			})
			.button({
				icons: {
					primary: 'ui-icon-circle-plus'
				}
			})
			.css({
				'margin-top': 0,
				'margin-bottom': 0,
				'margin-right': 0
			});

		// Valums file uploader
		var uploader = new qq.FineUploaderBasic({
			button: upload_button_pane[0], // connecting directly to the jQUery UI upload_button doesn't work
			callbacks: {
				onComplete: $.proxy(function(id, fileName, responseJSON) {
					this.refresh_grid();
				}, this)
			},
			debug: false,
			request: {
				endpoint: this.get_upload_path(),
				inputName: this.get_upload_fieldname(),
				params: {
					'title': this.get_upload_fieldname(),
					"csrfmiddlewaretoken": getCookie('csrftoken')
				},
				paramsInBody: true
			}
		});

		// reset button behavior
		upload_button_pane.css({
			'float': 'left',
			'margin-top': 8,
			'margin-bottom': 8
		});
	},

	create_delete_button: function() {
		var button_pane = this.uiDialog.parent().find('.ui-dialog-buttonpane');

		var delete_button_pane = $('<div/>').prependTo(button_pane)
			.attr({
				'id': 'delete-buttonpane'
			});

		var delete_button = $('<button type="button">' + gettext('Delete') + '</button>')
			.appendTo(delete_button_pane)
			.attr({
				'class': 'delete',
				'id': 'delete-file-button'
			})
			.button({
			})
			.css({
				'margin-top': 0,
				'margin-bottom': 0,
				'margin-right': 0
			});

		// reset button behavior
		delete_button_pane.css({
			'float': 'left',
			'margin-top': 8,
			'margin-bottom': 8
		});

		delete_button.addClass('ui-button-disabled ui-state-disabled');

		this.select_grid.bind('datagrid.select', function(e) {
			if (e.row.can_edit){
				delete_button.attr('disabled', '');
				delete_button.removeClass('ui-button-disabled ui-state-disabled');
			}
			else if (!delete_button.hasClass('ui-button-disabled ui-state-disabled')){
					delete_button.addClass('ui-button-disabled ui-state-disabled');
				}
		});

		var self = this;

		delete_button.bind('click', function() {
			var url = self.select_grid.simple_datagrid('getSelectedRow').url;

			$.ajax({
				url: url,
				type: 'DELETE',
				data: {},
				statusCode: {
					200: function(data) {
						alert(data);
						self.refresh_grid();
					},

					403: function(data) {
						alert(data);
					}
				}
			});
		});
	}
});


Cms.ImageSelectDialog = BaseFileSelectDialog.extend({

	defaults: {
		url: '/api/cms/images/',
		width: 540,
		height: 'auto',
		start_width: 480,
		start_height: 'auto'
	},


	// override default dialog window
	init_dialog: function() {
		// don't call _super, just call init_dialog_success at the end
		this.uiDialog.dialog('option', 'zIndex', 1200); // set z-index here, because it can't set by _super

		// enhance action button
		var action_button = this.uiDialog.parent().find(':button:contains("Action")');
		action_button.attr('id', 'action-button');

		action_button.find('.ui-button-text').text(gettext('Select'));

		action_button.attr('disabled', 'disabled');
		action_button.addClass('ui-button-disabled ui-state-disabled');

		this.uiDialog.dialog('option', 'title', gettext('Select an image'));

		this.init_dialog_success();
	},

	init_dialog_success: function(data) {

		var action_button = this.uiDialog.parent().find('#action-button');
		var search = '';
		var self = this;

		this.select_grid = $(document.createElement('table')).attr('id', 'ui-image-select-grid');
		this.image_select_filter = $(document.createElement('div')).attr('id', 'ui-image-select-filter');
		this.image_select_filter.append($(document.createElement('label')).attr({ id: 'ui-image-select-filter-label'}).text(gettext('Filter')));
		this.image_select_filter.append($(document.createElement('input')).attr({ id: 'ui-image-select-filter-input', name: 'filter', value: '', type: 'text' }));
		this.uiDialog.append(this.image_select_filter);
		this.uiDialog.append(this.select_grid);

		function thumbnail_formatter(value, row_data) {
			// insert the url that ckeditor looks for. Use HTML5 data attribute instead?
			// TODO: use image checksum for cache busting?
			var thumbnail_url = row_data.thumbnail_url;
			if (thumbnail_url === null) {
				thumbnail_url = row_data.image_url;
			}
			return '<span style="display: none;">' + row_data.image_url + '</span>' + '<img src="' + thumbnail_url + '?_c=' + encodeURIComponent(row_data.url) + '" title="' + row_data.title + '"/>';
		}

		this.select_grid.simple_datagrid({
			columns: [
				{title: gettext('Image'), key: 'image', on_generate: thumbnail_formatter},
				{title: gettext('Filename'), key: 'filename', on_generate: this.uneditables_formatter},
				{title: gettext('Size'), key: 'size'},
				{title: gettext('Updated'), key: 'updated'}
			],
			url: this.options.url,
			order_by: 'updated',
			sortorder: 'desc'
		});

		this.select_grid.bind('datagrid.select', function() {
			action_button.attr('disabled', '');
			action_button.removeClass('ui-button-disabled ui-state-disabled');
		});

		$('#ui-image-select-filter-input').keyup(function() {
			var new_search = $('#ui-image-select-filter-input').val();
			if (search != new_search) {
				search = new_search;
				self.select_grid.simple_datagrid('setParameter', 'search', search);
				self.select_grid.simple_datagrid('setCurrentPage', 1);
				self.refresh_grid();
			}
		});
	},

	get_upload_path: function() {
		return '/api/cms/images/';
	},

	get_selected_row: function() {
		return this.select_grid.simple_datagrid('getSelectedRow');
	},

	get_upload_fieldname: function() {
		return 'image';
	}
});


Cms.FileSelectDialog = BaseFileSelectDialog.extend({

	defaults: {
		url: '/api/cms/files/',
		width: 540,
		height: 'auto',
		start_width: 480,
		start_height: 'auto'
	},

	// override default dialog window
	init_dialog: function() {
		// don't call _super, just call init_dialog_success at the end
		this.uiDialog.dialog('option', 'zIndex', 1200); // set z-index here, because it can't set by _super

		// enhance action button
		var action_button = this.uiDialog.parent().find(':button:contains("Action")');
		action_button.attr('id', 'action-button');

		action_button.find('.ui-button-text').text(gettext('Select'));

		action_button.attr('disabled', 'disabled');
		action_button.addClass('ui-button-disabled ui-state-disabled');

		this.uiDialog.dialog('option', 'title', gettext('Select a file'));

		this.init_dialog_success();
	},

	init_dialog_success: function(data) {
		var action_button = this.uiDialog.parent().find('#action-button');
		var search = '';
		var self = this;

		this.select_grid = $(document.createElement('table')).attr('id', 'ui-file-select-grid');
		this.file_select_filter = $(document.createElement('div')).attr('id', 'ui-file-select-filter');
		this.file_select_filter.append($(document.createElement('label')).attr({ id: 'ui-file-select-filter-label'}).text(gettext('Filter')));
		this.file_select_filter.append($(document.createElement('input')).attr({ id: 'ui-file-select-filter-input', name: 'filter', value: '', type: 'text' }));
		this.uiDialog.append(this.file_select_filter);
		this.uiDialog.append(this.select_grid);

		this.select_grid.simple_datagrid({
			columns: [
				{title: gettext('Filename'), key: 'filename', on_generate: this.uneditables_formatter},
				{title: gettext('Updated'), key: 'updated'}
			],
			url: this.options.url,
			order_by: 'updated',
			sortorder: 'desc'
		});
		this.select_grid.bind('datagrid.select', function() {
			action_button.attr('disabled', '');
			action_button.removeClass('ui-button-disabled ui-state-disabled');
		});

		$('#ui-file-select-filter-input').keyup(function() {
			var new_search = $('#ui-file-select-filter-input').val();
			if (search != new_search) {
				search = new_search;
				self.select_grid.simple_datagrid('setParameter', 'search', search);
				self.select_grid.simple_datagrid('setCurrentPage', 1);
				self.refresh_grid();
			}
		});
	},

	get_upload_path: function() {
		return '/api/cms/files/';
	},

	action_click: function() {
		// do something
	},

	cancel_click: function() {
		this.destroy();
	},

	get_selected_row: function() {
		return this.select_grid.simple_datagrid('getSelectedRow');
	}
});


var adminPage = {
	init_backend: function() {
		enhance_textareas($(document.body), false);
	},

	init: function() {
		this.init_backend();
	}
};

$(window).ready(function() {
	adminPage.init();
});

})(cms_jQuery); // end of jQuery noConflict mode
