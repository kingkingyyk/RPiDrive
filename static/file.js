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

function enableDialogButtons() {
    $("#file-operation-name").removeClass("disabled");
    $("#file-operation-dialog-close").removeClass("disabled");
}

function disableDialogButtons() {
    $("#file-operation-name").addClass("disabled");
    $("#file-operation-dialog-close").addClass("disabled");
}


function openNewFolderDialog() {
    prepareDialog(
        "Create New Folder",
        `<input type="text" id="new-folder-name">`,
        "Create",
        function () {
            disableDialogButtons();
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
                enableDialogButtons();
            });
    });
    $("#new-folder-name").val("New Folder");
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
    prepareDialog("Rename "+selectedFileName,
                  `<input type="text" id="new-name">`,
                  "Rename",
                  function() {
                        disableDialogButtons();
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
                            enableDialogButtons();
                        });
                  }
    );
    $("#new-name").val(selectedFileName);
}

function openMoveDialog() {
    prepareDialog("Move items",
                  getLoaderCode("small"),
                  "Move",
                  function() {
                        disableDialogButtons();
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
                                enableDialogButtons();
                            });
                        }
                  }
    );
    $.get(getCurrentURL() + 'list-folders/1')
    .done(function(data) {
        $("#file-operation-content").html(data);
        $("#file-operation-name").removeClass("disabled");
    })
    .fail(function() {
        $("#file-operation-error").text(data["responseJSON"]["error"]);
    })
}

function openDeleteDialog() {
    prepareDialog(  "Confirm to delete selected items?",
                    "", "Delete",
                    function() {
                        disableDialogButtons();
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
                                enableDialogButtons();
                            });
                        }
                    });
}

function openUploadDialog() {
    prepareDialog( "Upload Files",
                    `<form method="post" id="upload-file" enctype="multipart/form-data">
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
                      </form>`,
                    "Upload",
                    function () {
                        disableDialogButtons();
                        $.ajax({
                                type: "POST",
                                url: "upload/"+currentDirectory,
                                data: new FormData($('#upload-file')[0]),
                                cache: false,
                                contentType: false,
                                processData: false,
                                xhr: function () {
                                    var xhr = new window.XMLHttpRequest();
                                    xhr.upload.addEventListener("progress", function(evt) {
                                        if (evt.lengthComputable) {
                                            var percentComplete = evt.loaded / evt.total;
                                            percentComplete = parseInt(percentComplete * 100);
                                            $("#file-operation-info").text(percentComplete.toString()+"%");
                                        }
                                        if (percentComplete === 100) {
                                            $("#file-operation-info").html(getLoaderCode("small"));
                                        }
                                    }, false);

                                    return xhr;
                                }
                        }).done(function() {
                            loadDirectory(currentDirectory);
                        }).fail(function(data, textStatus, errorThrown) {
                            errorText = errorThrown;
                            if (data["responseJSON"] != null) errorText = data["responseJSON"]["error"];
                            $("#file-operation-info").html("");
                            $("#file-operation-error").text(errorText);
                        }).always(function() {
                            enableDialogButtons();
                        });
                    }
                );
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