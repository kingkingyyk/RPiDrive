function updateSyncSchedule() {
    days = "";
    $(".sync-schedule-days").each(function() {
        if ($(this).is(':checked')) {
            days += $(this).attr("day") + ",";
        }
    });
    if (days.length > 0) days = days.substring(0, days.length-1);

    url = window.location.href + '/update-sync-schedule';
    $.post( url,
        { 'days': days, 'period': parseInt($("#sync-schedule-period").val()), 'csrfmiddlewaretoken': csrf_token })
    .done(function() {
        location.reload();
    })
    .fail(function(data) {
        alert(data["responseJSON"]["error"]);
    })
}