function loadOngoingTasks(loop) {
    currOngoingTasks = $("#ongoing-tasks").html()
    $.get(getCurrentURL()+"ongoing-tasks")
    .done(function(data) {
        $("#ongoing-tasks").html(data);
        if (loop) {
            setTimeout(loadOngoingTasks,3000,true);
        }
    });
}


function prepareDialog(title, content, buttonName, buttonResponse) {
    $("#file-operation-error").html("");
    $("#file-operation-info").html("");
    $("#file-operation-name").removeClass("disabled");

    $("#file-operation-title").html(title)
    $("#file-operation-content").html(content);
    $("#file-operation-name").html(buttonName);
    $("#file-operation-name").off("click");
    $("#file-operation-name").click(buttonResponse);
    M.Modal.getInstance($('#file-operation-dialog')).open();
}



function openDownloadFileDialog() {
    prepareDialog("Download File from URL", `<div class="row">
                                                  <div class="input-field col s12">
                                                    <input id="download-file-url" type="text" class="validate">
                                                    <label for="download-file-url">URL</label>
                                                  </div>
                                                </div>
                                                <div class="row">
                                                  <div class="input-field col s12">
                                                    <input id="download-file-name" type="text" class="validate">
                                                    <label for="download-file-name">Filename</label>
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
                                                </div>`,
                "Download", function () {
                    $("#file-operation-name").addClass("disabled");
                    url = getCurrentURL() + 'downloader/add';

                    dl_url = $("#download-file-url").val();
                    filename = $("#download-file-name").val();
                    auth = $("#download-file-auth").prop("checked").toString();
                    auth_user = $("#download-file-auth-user").val();
                    auth_password = $("#download-file-auth-password").val();

                    $.post( url,
                        { 'url': dl_url,
                          'filename': filename,
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
    $("#download-file-auth").click(() => {
        if ($("#download-file-auth").prop("checked")) {
            $("#download-file-auth-user").removeAttr("disabled");
            $("#download-file-auth-password").removeAttr("disabled");
        } else {
            $("#download-file-auth-user").attr("disabled", "");
            $("#download-file-auth-password").attr("disabled", "");
        }
    });
}

function stopDownload(downloadID) {
     $.post( getCurrentURL()+'downloader/cancel',
        { 'id': downloadID,
          'csrfmiddlewaretoken': csrf_token })
    .done(function() {
        loadOngoingTasks(false);
    })
}

$(function() {
    loadOngoingTasks(true);
});