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
        currentDirectory=folderId;
    })
    .fail(function(data) {
        $(".file-list").html("<h2>Load failed!</h2>");
    });
    window.history.pushState('', '', getCurrentURL()+'?folder='+folderId);
}

function loadFile(fileId, fileName, fileType) {
    url = getCurrentURL() + 'download/'+fileId;
    var previewableTypes = ["movie", "music", "picture", "text"];
    if (previewableTypes.indexOf(fileType)>=0) {
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

function clearPreview() {
    $("#preview-screen").html("");
}

$(function() {
    M.AutoInit();
    loadDirectory(currentDirectory);
});


