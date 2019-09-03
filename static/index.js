function getCurrentURL() {
    curr_url = window.location.href;
    return curr_url.substring(0, curr_url.indexOf('?'));
}

function getLoaderCode() {
    return `<div class="preloader-wrapper big active">
            <div class="spinner-layer spinner-red-only">
              <div class="circle-clipper left">
                <div class="circle"></div>
              </div><div class="gap-patch">
                <div class="circle"></div>
              </div><div class="circle-clipper right">
                <div class="circle"></div>
              </div>
            </div>
          </div>`;
}

function loadDirectory(folderId) {
    $(".file-list").html(getLoaderCode());

    $.get("navigate/"+folderId)
    .done(function(data) {
        $(".file-list").html(data);
        //$(".file-list").removeClass("file-list").addClass("file-list");
        currentDirectory=folderId;
    })
    .fail(function(data) {
        $(".file-list").html("<h2>Load failed!</h2>");
    });
    window.history.pushState('', '', getCurrentURL()+'?folder='+folderId);
}

function loadFile(fileId, fileName, fileType) {
    url = getCurrentURL() + 'download/'+fileId;
    if (fileType != "none") {
        $("#preview-title").html(fileName);
        if (fileType == "movie") {
            $("#preview-screen").html("<video class='responsive-video' controls autoplay><source src='"+url+"'></video>");
        } else if (fileType == "music") {
            $("#preview-screen").html("<audio class='responsive-video' controls autoplay><source src='"+url+"'></audio>");
        } else if (fileType == "picture") {
            $("#preview-screen").html("<img style='width:100%' src='"+url+"'>");
        } else if (fileType == "text") {
            $("#preview-screen").html(getLoaderCode());
            $.get(url, function(data) {
                $("#preview-screen").html("<pre style='font-size: 12px'><code>"+data+"</code></pre>");
            });
        }

        $("#btnDownloadFromPreview").attr('href', url);
        M.Modal.getInstance($('#preview')).onCloseEnd = () => {
            clearPreview();
        };
        M.Modal.getInstance($('#preview')).open();
    } else {
        window.open(url, '_blank');
    }
}

function loadOngoingTasks() {
    currOngoingTasks = $("#ongoing-tasks").html()
    $.get(getCurrentURL()+"ongoing-tasks")
    .done(function(data) {
        $("#ongoing-tasks").html(data);
    });
}

function setupFileSelection() {
    $("#fileSelectionAll").change(function() {
        val = $("#fileSelectionAll").is(":checked");
        $(".fileSelectionSingle").each(function() {
            $(this).prop("checked", val);
        });
        updateFileActionButtons();
    });
    $(".fileSelectionSingle").change(function() {
        updateFileActionButtons();
    });
}

function updateFileActionButtons() {
    selectionCount = 0;
    $(".fileSelectionSingle").each(function() {
        if ($(this).is(":checked")) {
            selectionCount++;
        }
    });
    $(".file-actions").each(function() {
        $(this).addClass("disabled");
    });
    if (selectionCount == 1) {
         $(".file-actions-single").each(function() {
            $(this).removeClass("disabled");
        });
    } else if (selectionCount > 1) {
         $(".file-actions-many").each(function() {
            $(this).removeClass("disabled");
        });
    }
}

function copyShareLink() {
    fileId = "";
    fileType = "";
    $(".fileSelectionSingle").each(function() {
        if ($(this).is(":checked")) {
            fileId = $(this).attr("file-id");
            fileType = $(this).attr("file-type");
        }
    });

    if (fileType == "Folder") {
        url = getCurrentURL() + '?folder='+fileId;
    } else {
        url = getCurrentURL() + 'download/'+fileId;
    }

    var $temp = $("<input>");
    $("body").append($temp);
    $temp.val(url).select();
    document.execCommand("copy");
    $temp.remove();

    M.toast({html: 'URL copied to clipboard!'})
}

function clearPreview() {
    $("#preview-screen").html("");
}

function openNewFolderDialog() {
    $("#file-operation-content").html(`
            <h4 id="file-operation-title">Create New Folder</h4>
            <input type="text" id="new-folder-name">
        `);
    $("#new-folder-name").val("New Folder");
    $("#file-operation-name").text("Create");
    $("#file-operation-error").text("");
    $("#file-operation-name").click(function () {
        $("#file-operation-name").addClass("disabled");
        url = getCurrentURL() + 'create-folder/'+currentDirectory;
        $.post( url,
            { 'name': $("#new-folder-name").val(), 'csrfmiddlewaretoken': csrf_token })
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

function openRenameDialog() {
    selectedFileId = "";
    selectedFileName = "";
    $(".fileSelectionSingle").each(function() {
        if ($(this).is(":checked")) {
            selectedFileId = $(this).attr("file-id");
            selectedFileName = $(this).attr("file-name");
        }
    });
    $("#file-operation-content").html(`
            <h4 id="file-operation-title">Rename `+selectedFileName+`</h4>
            <input type="text" id="new-name">
        `);
    $("#new-name").val(selectedFileName);
    $("#file-operation-name").text("Rename");
    $("#file-operation-error").text("");
    $("#file-operation-name").click(function () {
        $("#file-operation-name").addClass("disabled");
        url = getCurrentURL() + 'rename/'+selectedFileId;
        $.post( url,
            { 'name': $("#new-name").val(), 'csrfmiddlewaretoken': csrf_token })
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

function openMoveDialog() {
    str = `<h4 id="file-operation-title">Move items</h4>`;
    $("#file-operation-content").html(str);
    $("#file-operation-name").text("Move");
    $("#file-operation-name").addClass("disabled");

    $.get(getCurrentURL() + 'list-folders/1')
    .done(function(data) {
        $("#file-operation-content").html(str+data);
        $("#file-operation-name").removeClass("disabled");
    })
    .fail(function() {
        $("#file-operation-error").text(data["responseJSON"]["error"]);
    })

    $("#file-operation-name").click(function () {
        $("#file-operation-name").addClass("disabled");
        selectedFileObjIds = "";
        $(".fileSelectionSingle").each(function() {
            if ($(this).is(":checked")) {
                selectedFileObjIds = selectedFileObjIds + $(this).attr("file-id") + ",";
            }
        });
        if (selectedFileObjIds.length > 0) {
            selectedFileObjIds = selectedFileObjIds.slice(0,-1)
            url = getCurrentURL() + 'move';
            $.post( url,
                { 'to-move-ids': selectedFileObjIds, 'destination-id': currMoveDestinationDirectory, 'csrfmiddlewaretoken': csrf_token })
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
        }
    });

    M.Modal.getInstance($('#file-operation-dialog')).open();
}

function openDeleteDialog() {
    $("#file-operation-content").html(`
            <h4 id="file-operation-title">Confirm to delete selected items?</h4>
        `);
    $("#file-operation-name").text("Delete");
    $("#file-operation-name").click(function () {
        $("#file-operation-name").addClass("disabled");
        selectedFileObjIds = "";
        $(".fileSelectionSingle").each(function() {
            if ($(this).is(":checked")) {
                selectedFileObjIds = selectedFileObjIds + $(this).attr("file-id") + ",";
            }
        });
        if (selectedFileObjIds.length > 0) {
            selectedFileObjIds = selectedFileObjIds.slice(0,-1)
            url = getCurrentURL() + 'delete';
            $.post( url,
                { 'delete-ids': selectedFileObjIds, 'csrfmiddlewaretoken': csrf_token })
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
        }
    });
    M.Modal.getInstance($('#file-operation-dialog')).open();
}

function openUploadDialog() {
    $("#file-operation-content").html(`
            <h4 id="file-operation-title">Upload Files</h4>
                <form method="post" id="upload-file" enctype="multipart/form-data">
                <input type="hidden" name="csrfmiddlewaretoken" value="`+csrf_token+`">
                <div class="file-field input-field">
                  <div class="btn red lighten-1">
                    <span>File</span>
                    <input type="file" name="files-to-upload" multiple>
                  </div>
                  <div class="file-path-wrapper">
                    <input class="file-path validate" type="text" placeholder="Upload one or more files">
                  </div>
                </div>
              </form>
        `);
    $("#file-operation-name").text("Upload");
    $("#file-operation-name").click(function () {
        $("#file-operation-name").addClass("disabled");
        $("#upload-file").attr('action', 'upload/'+currentDirectory);
        $("#upload-file").submit();
    });
    M.Modal.getInstance($('#file-operation-dialog')).open();
}

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


$(function() {
    M.AutoInit();
    loadDirectory(currentDirectory);
    loadOngoingTasks();
    setInterval(loadOngoingTasks,5000);
});


