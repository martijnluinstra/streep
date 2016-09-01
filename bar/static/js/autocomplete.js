var members = new Bloodhound({ 
    datumTokenizer: Bloodhound.tokenizers.obj.whitespace('name'), 
    queryTokenizer: Bloodhound.tokenizers.whitespace, 
    identify: function(obj) { return obj.id; },
    remote: {
		url: window.urls.auto_complete_members + '?name=%QUERY',
		wildcard: '%QUERY'
	}
}); 

$('#name.typeahead').typeahead({
    highlight: true
}, { 
    name: 'members',
    display: 'name',
    source: members,
    templates: {
    	suggestion: function(member){
    		return '<div><strong>'+ member.name +'</strong> – ' + member.iban + '</div>';
    	}
    }
});

$('#name.typeahead').bind('typeahead:select typeahead:autocomplete', function(ev, suggestion) {
    $('#member_id').val(suggestion.id);
    $('#address').val(suggestion.address);
    $('#city').val(suggestion.city);
	$('#email').val(suggestion.email);
	$('#phone').val(suggestion.phone);
    $('#iban').val(suggestion.iban);
    $('#bic').val(suggestion.bic);
	$('#birthday').val(suggestion.birthday);
});
