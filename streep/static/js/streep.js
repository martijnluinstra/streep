var current = {};
var delta = {};
var model = {
    purchases: [],
    undos: []
};
var timers = {};

$('.table-users tr').each(function() {
    current[this.id] = parseInt($(this).data('spend-amount'));
});

$(".table-users button[data-type^='purchase']").click(function(evt){
    evt.preventDefault();
    // Get me some data
    var field = $(this).closest('tr').find('td').get(1);
    var user_id = $(this).data('user-id');
    var product_id = $(this).data('product-id');
    var product_price = $(this).data('price');
    var is_eligible = $(this).data('is-eligible');

    if (!is_eligible){
        var proceed = confirm($(this).closest('tr').find('td').get(0).innerHTML + ' is too young to buy this product! Are you sure you want to continue?');
        if(!proceed) return;
    }

    // Update the users delta and current amount of x-es
    model['purchases'].push({user_id: user_id, product_id: product_id, price: product_price});
    delta[user_id] = (delta[user_id] || 0) + product_price;
    $(field).text("€ "+((current[user_id] + delta[user_id])/100).toFixed(2));

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
            timeout: 3000
        }).fail(function(response){
            model[item].concat(submitted_items);
            for(var i in submitted_items){
                var user_id = i['user_id'];
                delta[user_id] = (delta[user_id] || 0) + i['price'];
                current[user_id] -= i['price'];
            }
            alert('Something went wrong? See the console, or ask Jelmer or Martijn');
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

$(".table-users button[data-type^='history']").click(function(evt){
    evt.preventDefault();
    var user_id = $(this).data('user-id');
    url='/users/' + user_id + '/history';

    $.get(url, {timeout: 3000}, function( data ) {
            show_history_modal($(data).filter('.user-panel'));
        }).fail(function(response){
        alert('Something went wrong? See the console, or ask Jelmer or Martijn');
    });
});

function show_history_modal(data){
    title = data.find('.panel-title').html();
    body = data.find('.table-users');
    body.find('button').click(function(evt){
        evt.preventDefault();

        var user_id = $(this).data('user-id');
        var purchase_id = $(this).data('purchase-id');
        var product_price = $(this).data('price')*-1;
        var field = $('.table-users tr#'+user_id).find('td').get(1);

        // Update the users delta and current amount of x-es
        model['undos'].push({user_id: user_id, purchase_id: purchase_id, price: product_price});
        delta[user_id] = (delta[user_id] || 0) + product_price;
        $(field).text("€ "+((current[user_id] + delta[user_id])/100).toFixed(2));

        // If there is a sync-request queued for this user, delete it.
        if (timers['undos'])
            clearTimeout(timers['undos']);

        // Queue a sync-request for this user
        timers['undos'] = setTimeout(create_sync_task('/purchase/undo', 'undos'), 1000);

        $(this).prop('disabled', true);
    });
    $('#streepModal').find('.modal-title').html(title);
    $('#streepModal').find('.modal-body').empty().append(body);
    $('#streepModal').modal('show');
};