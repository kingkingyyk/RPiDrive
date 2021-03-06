function getCurrentURL() {
    curr_url = window.location.href;
    return curr_url.substring(0, curr_url.indexOf('?'));
}

function getLoaderCode(size) {
    return `<div class="preloader-wrapper `+size+` active">
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
    $(".file-list").html(getLoaderCode("big"));
    updateFileActionButtons();
    $.get("navigate/"+folderId)
    .done(function(data) {
        $(".file-list").html(data);
        currentDirectory=folderId;
        updateFileActionButtons();
    })
    .fail(function(data) {
        $(".file-list").html("<h2>Load failed!</h2>");
    });
    window.history.pushState('', '', getCurrentURL()+'?folder='+folderId);
}

mediaCastURL = "";
mediaCastMime = "";
castHTML = "";
function loadFile(fileId, fileName, fileType, mimeType) {
    url = getCurrentURL() + "download/"+fileId;
    var previewableTypes = ["movie", "music", "picture", "code"];
    if (previewableTypes.indexOf(fileType)>=0) {
        $("#preview-title").html(fileName);
        if (fileType == "movie") {
            mediaCastURL = url;
            mediaCastMime = mimeType;
            $("#preview-screen").html("<video class='responsive-video' controls autoplay><source src='"+url+"'></video>"+castHTML);
        } else if (fileType == "music") {
            $("#preview-screen").html("<audio class='responsive-video' controls autoplay><source src='"+url+"'></audio>"+castHTML);
            mediaCastURL = url;
            mediaCastMime = mimeType;
        } else if (fileType == "picture") {
            mediaCastURL = url;
            mediaCastMime = mimeType;
            $("#preview-screen").html("<img style='width:100%' src='"+url+"'>"+castHTML);
        } else if (fileType == "code") {
            $("#preview-screen").html(getLoaderCode("big"));
            $.get(url, function(data) {
                $("#preview-screen").html("<pre style='font-size: 12px;'><code>"+data+"</code></pre>");
                hljs.highlightBlock($("#preview-screen pre code").get(0));
            });
        }

        $("#btnDownloadFromPreview").attr('href', url);

        M.Modal.getInstance($('#preview')).options.onCloseEnd = function() {
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

function requestSearchResultAutoComplete(val, success, failure) {
    $.get("search-hint", {"name":val})
    .done(success)
    .fail(failure);
}

function displaySearchResult(val) {
    $(".file-list").html(getLoaderCode("big"));
    updateFileActionButtons();
    $.get("search", {"name":val})
    .done(function(data) {
        $(".file-list").html(data);
        updateFileActionButtons();
    })
    .fail(function(data) {
        $(".file-list").html("<h2>Load failed!</h2>");
    });
    window.history.pushState('', '', getCurrentURL()+'?search='+val);
}


function setupSearch() {
    searchInput = $("#search-text-input");
    if (searchInput.attr("registered") == null) {
        searchInput.attr("registered", 1);
        searchInput.keyup(function(e) {
            if (e.keyCode == 8 || (e.keyCode >= 35 && e.keyCode <= 40)) return;
            val = searchInput.val();
            if (val != null && val.length > 0) {
                if (e.key == "Enter") displaySearchResult(val);
                else {
                    var searchInputM = M.Autocomplete.getInstance(searchInput);
                    searchInputM.open();
                    requestSearchResultAutoComplete(searchInput.val(), function(data) {
                        searchInputM.updateData(data);
                    }, null);
                }
            } else loadDirectory(currentDirectory);
        });
        searchInput.click(function() {
            if (val != null && val.length > 0) searchInput.keyup();
        })
    }
    M.Autocomplete.getInstance(searchInput).options.onAutocomplete = function(val) {
        displaySearchResult(val);
    };
}

function initUI() {
    M.AutoInit();
    M.Modal.init($('#file-operation-dialog'), {
        dismissible: false,
    });
    setupSearch();
}

$(function() {
    $.ajaxSetup({ cache: false });
    //Fix back button not working due to push state
    $(window).bind('popstate', function(){
        window.location.href = window.location.href;
    });

    initUI();
    loadDirectory(rootDirectory);
});