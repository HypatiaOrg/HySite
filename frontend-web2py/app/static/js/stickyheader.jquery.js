jQuery(document).ready(function ($) {
	var tables = $('table.stickyHeader');
	tables.each(function(i){
		var table = tables[i];
		var tableClone = $(table).clone(true).empty().removeClass('stickyHeader');
		var theadClone = $(table).find('thead').clone(true);
		var stickyHeader =  $('<div></div>').addClass('stickyHeader hide').attr('aria-hidden', 'true');
		stickyHeader.append(tableClone).find('table').append(theadClone);
		$(table).after(stickyHeader);
		
		setUpHeader = function() {
			var tableWidth = $(table).width() + Number($(table).css('padding-left').replace(/px/ig,"")) + Number($(table).css('padding-right').replace(/px/ig,"")) + Number($(table).css('border-left-width').replace(/px/ig,"")) + Number($(table).css('border-right-width').replace(/px/ig,""));
			
			var headerCells = $(table).find('thead th');
			
			var stickyHeaderCells = stickyHeader.find('th');
			stickyHeader.css('width', tableWidth);
			var cellWidths = [];
			for (var i = 0, l = headerCells.length; i < l; i++) {
				cellWidths[i] = $(headerCells[i]).width() + 17;
			}
			for (var i = 0, l = headerCells.length; i < l; i++) {
				$(stickyHeaderCells[i]).css('width', cellWidths[i]);
			}
		};
		setUpHeader();
		$(window).resize(setUpHeader);
		
		var tableHeight = $(table).height();
		var headerCells = $(table).find('thead th');
		var headerCellHeight = $(headerCells[0]).height();
		var cutoffTop = $(table).offset().top;
		var cutoffBottom = tableHeight + cutoffTop - headerCellHeight;
		var no_fixed_support = false;
		if (stickyHeader.css('position') == "absolute") {
			no_fixed_support = true;
		}
		
		var adjustHeaders = function() { 
			var cutoffLeft = $(table).offset().left;
			stickyHeader.css('left',-$(window).scrollLeft()+cutoffLeft);
			var currentPosition = $(window).scrollTop();
			if (currentPosition > cutoffTop && currentPosition < cutoffBottom) {
				stickyHeader.removeClass('hide');
				if (no_fixed_support) {
					stickyHeader.css('top', currentPosition + 'px');
				}
			}
			else {
				stickyHeader.addClass('hide');
			}
		}
		
		$(window).scroll(adjustHeaders);
		setInterval(adjustHeaders,100);
	});
});
