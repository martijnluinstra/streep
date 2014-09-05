var current = {};
var delta = {};
var model = {
    purchases: [],
    undos: []
};
var timers = {};
var config = {
    error_message: 'Something went wrong? See the console, or ask Martijn!',
    history_size: 10
};

$('#view-users .table-streep tr').each(function() {
    current[this.id] = parseInt($(this).data('spend-amount'));
});

$("#view-users .table-streep button[data-type^='purchase']").click(function(evt){
    evt.preventDefault();
    // Get me some data
    var field = $(this).closest('tr').find('td').get(1);
    var spinner = $(this).closest('td').find('.spinner').get(0);
    var user_id = $(this).data('user-id');
    var product_id = $(this).data('product-id');
    var product_price = $(this).data('price');
    var is_eligible = $(this).data('is-eligible');
    var amount = parseInt($($(spinner).find('input').get(0)).val());

    if (isNaN(amount)) amount = 1;

    if (!is_eligible){
        var proceed = confirm($(this).closest('tr').find('td').get(0).innerHTML + ' is too young to buy this product! Are you sure you want to continue?');
        if(!proceed) return;
    }

    // Update the users delta and current amount of x-es
    for(var i=0;i<amount;i++){
        model['purchases'].push({user_id: user_id, product_id: product_id, price: product_price});
        delta[user_id] = (delta[user_id] || 0) + product_price;
    }
    $(field).text("€ "+((current[user_id] + delta[user_id])/100).toFixed(2));

    //reset spinner
    spinner_reset(spinner);

    // If there is a sync-request queued for this user, delete it.
    if (timers['purchases'])
        clearTimeout(timers['purchases']);

    // Queue a sync-request for this user
    timers['purchases'] = setTimeout(create_sync_task('/purchase', 'purchases'), 1000);
});

function create_sync_task(url, item) {
    return function() {
        // Run the request
        var submitted_items = model[item];
        $.ajax({
            url: url,
            type: "POST",
            data: JSON.stringify(model[item]),
            contentType: "application/json",
            timeout: 5000
        }).fail(function(response){
            model[item].concat(submitted_items);
            for(var i in submitted_items){
                var user_id = i['user_id'];
                delta[user_id] = (delta[user_id] || 0) + i['price'];
                current[user_id] -= i['price'];
            }
            alert(config['error_message']);
        });

        console.log('Submitted', model[item], 'to', url);

        // commit locally
        for(var i in model[item]){
            current[i['user_id']] += i['price'];
            delete delta[i['user_id']];
        }
        model[item] = new Array();
        delete timers[item];
    }
};

$("#view-users  .table-streep button[data-type^='history']").click(function(evt){
    evt.preventDefault();
    var user_id = $(this).data('user-id');
    url='/users/' + user_id + '/history?show='+config['history_size'];

    $.get(url, {timeout: 3000}, function( data ) {
            show_history_modal($(data).find('.streep-panel'), user_id);
        }).fail(function(response){
        alert(config['error_message']);
    });
});

function show_history_modal(data, user_id){
    title = data.find('.panel-title').html();
    body = data.find('.table-streep');
    body.find("a[data-type^='undo']").click(function(evt){
        evt.preventDefault();

        var user_id = $(this).data('user-id');
        var purchase_id = $(this).data('purchase-id');
        var product_price = $(this).data('price')*-1;
        var field = $('.table-streep tr#'+user_id).find('td').get(1);

        // Update the users delta and current amount of x-es
        model['undos'].push({user_id: user_id, purchase_id: purchase_id, price: product_price});
        delta[user_id] = (delta[user_id] || 0) + product_price;
        $(field).text("€ "+((current[user_id] + delta[user_id])/100).toFixed(2));

        // If there is a sync-request queued for this user, delete it.
        if (timers['undos'])
            clearTimeout(timers['undos']);

        // Queue a sync-request for this user
        timers['undos'] = setTimeout(create_sync_task('/purchase/undo', 'undos'), 1000);

        $(this).addClass('disabled');
    });
    var btn_more = $('<a href="/users/' + user_id + '/history" class="btn btn-default">Complete history</a>');
    btn_more.click(leave_page);
    $('#streepModal').find('.modal-title').show().html(title);
    $('#streepModal').find('.modal-body').hide().empty();
    $('#streepModal').find('.modal-table').show().empty().append(body);
    $('#streepModal').find('.modal-footer').show().empty().append(btn_more).append('<button class="btn btn-primary" data-dismiss="modal">Ok</button>');
    $('#streepModal').find('.modal-dialog').removeClass("modal-lg");
    $('#streepModal').modal('show');
};

/* Search */

// Case insensitive contains filter
jQuery.expr[':'].containsNCS = function(a, i, m) {
  return jQuery(a).text().toUpperCase()
      .indexOf(m[3].toUpperCase()) >= 0;
};

$('#view-users  #search').focus();
$(document).click(function(evt) { 
    if (! $(evt.target).is( ".spinner input" ))
        $('#search').focus();
});

$('#view-users  #search').keyup(function() {
    var query = $(this).val();
    $('.table-streep tbody tr').hide();
    $('.table-streep tbody tr td:first-child:containsNCS('+ query +')').closest('tr').show();
});

/* FAQ */

$(".header button[data-type^='faq']").click(function(evt){
    evt.preventDefault();
    url='/faq';
    $.get(url, {timeout: 3000}, function( data ) {
            show_info_modal($(data).find('.streep-panel'));
        }).fail(function(response){
        alert(config['error_message']);
    });
});

function show_info_modal(data){
    title = data.find('.panel-title').html();
    body = data.find('.panel-body').html();
    $('#streepModal').find('.modal-title').show().html(title);
    $('#streepModal').find('.modal-body').show().html(body);
    $('#streepModal').find('.modal-table').hide().empty();
    $('#streepModal').find('.modal-footer').show().html('<button class="btn btn-primary" data-dismiss="modal">Ok</button>');
    $('#streepModal').find('.modal-dialog').addClass("modal-lg");
    $('#streepModal').modal('show');
};

/* Spinner */

$('.spinner .btn:first-of-type').click(function(evt) {
    evt.preventDefault();
    spinner_update($(this).closest('.spinner'), 1);
});
$('.spinner .btn:last-of-type').click(function(evt) {
    evt.preventDefault();
    spinner_update($(this).closest('.spinner'), -1);
});
    
$('.spinner input').keyup(function(evt) {
    if(isNaN(parseInt($(this).val())) && $(this).val()!='') $(this).val(1);
    spinner_set_multiple($(this).closest('.spinner'));
});

function spinner_reset(spinner){
    $($(spinner).find('input').get(0)).val(1);
    spinner_set_multiple(spinner);
}

function spinner_update(spinner, mod){
    var input = $(spinner).find('input').get(0);
    var value = parseInt($(input).val(), 10) + mod;
    if(isNaN(value)) value = 1;
    if($(input).data('min') !== undefined) value = (value < $(input).data('min') ? $(input).data('min') : value);
    if($(input).data('max') !== undefined) value = (value > $(input).data('max') ? $(input).data('max') : value);
    $(input).val(value);
    spinner_set_multiple(spinner);
}

function spinner_set_multiple(spinner){
    if(parseInt($($(spinner).find('input').get(0)).val())>1){
        $(spinner).closest('tr').find("button[data-multiple='false']").prop('disabled', true);
    }else{
       $(spinner).closest('tr').find("button[data-multiple='false']").prop('disabled', false); 
    }
}

$('.block-screen').hide();

$("#view-users a").click(leave_page);

function leave_page(evt){
    evt.preventDefault();
    if (timers['purchases']){
        clearTimeout(timers['purchases']);
        var task = create_sync_task('/purchase', 'purchases');
        task();
    }
    if (timers['undos']){
        clearTimeout(timers['undos']);
        var task = create_sync_task('/purchase/undo', 'undos');
        task();
    }

    var target = $(this).attr('href');

    if (timers['leave'])
        clearInterval(timers['leave']);

    if ($.active>0){
        $('.block-screen').show();
        timers['leave'] = setInterval(function(){
            if ($.active==0){
                $('.block-screen').hide();
                clearInterval(timers['leave']);
                window.location = target;
            }
        }, 250);
    }else{
        window.location = target;
    }
}