function openDownloadFileDialog() {
    $("#file-operation-content").html(`
        <h4 id="file-operation-title">Download File from URL</h4>
        <div class="row">
          <div class="input-field col s12">
            <input id="download-file-url" type="text" class="validate">
            <label for="download-file-url">URL</label>
          </div>
        </div>
        <label>
          <input type="checkbox" class="filled-in checkbox-red" id="download-file-auth" />
          <span>Authentication</span>
        </label>
        <div class="row">
          <div class="input-field col s12">
            <input id="download-file-auth-user" type="text" disabled>
            <label for="download-file-auth-user">Username</label>
          </div>
        </div>
        <div class="row">
          <div class="input-field col s12">
            <input id="download-file-auth-password" type="password" disabled>
            <label for="download-file-auth-password">Password</label>
          </div>
        </div>
    `);
    $("#download-file-auth").click(() => {
        if ($("#download-file-auth").prop("checked")) {
            $("#download-file-auth-user").removeAttr("disabled");
            $("#download-file-auth-password").removeAttr("disabled");
        } else {
            $("#download-file-auth-user").attr("disabled", "");
            $("#download-file-auth-password").attr("disabled", "");
        }
    });
    $("#file-operation-name").text("Download");
    $("#file-operation-name").click(function () {
        $("#file-operation-name").addClass("disabled");
        url = getCurrentURL() + 'downloader/add';

        dl_url = $("#download-file-url").val();
        auth = $("#download-file-auth").prop("checked").toString();
        auth_user = $("#download-file-auth-user").val();
        auth_password = $("#download-file-auth-password").val();

        $.post( url,
            { 'url': dl_url,
              'auth': auth,
              'auth-user': auth_user,
              'auth-password': auth_password,
              'destination-folder': currentDirectory,
              'csrfmiddlewaretoken': csrf_token })
        .done(function() {
            M.Modal.getInstance($('#file-operation-dialog')).close();
            loadDirectory(currentDirectory);
        })
        .fail(function(data) {
            $("#file-operation-error").text(data["responseJSON"]["error"]);
        })
        .always(function() {
            $("#file-operation-name").removeClass("disabled");
        });
    });
    M.Modal.getInstance($('#file-operation-dialog')).open();
}

function stopDownload(downloadID) {
     $.post( getCurrentURL()+'downloader/cancel',
        { 'id': downloadID,
          'csrfmiddlewaretoken': csrf_token })
    .done(function() {
        loadOngoingTasks();
    })
}

$(function() {
    loadOngoingTasks();
    setInterval(loadOngoingTasks,5000);
});