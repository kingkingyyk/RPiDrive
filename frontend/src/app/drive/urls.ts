import { setupTestingRouter } from "@angular/router/testing";

export abstract class Url {
    public static getRootURL(): string {
        return 'drive';
    }
    public static getSetupRelURL(): string {
        return 'setup';
    }
    public static getSetupAbsURL(): string {
        return this.getRootURL() + '/' + this.getSetupRelURL();
    }
    public static getLoginRelURL(): string {
        return 'login';
    }
    public static getLoginAbsURL(): string {
        return this.getRootURL() + '/' + this.getLoginRelURL();
    }
    public static getFolderRelURL(): string {
        return 'folder';
    }
    public static getFolderAbsURL(): string {
        return this.getRootURL() + '/' + this.getFolderRelURL();
    }
    public static getSpecificFolderAbsURL(folderId: string): string {
        return this.getRootURL() + '/' + this.getFolderRelURL() + '/' + folderId;
    }
    public static getMenuRelURL(): string {
        return 'menu';
    }
    public static getMenuAbsURL(): string {
        return this.getRootURL() + '/' + this.getMenuRelURL();
    }
    public static getSearchAbsURL(): string {
        return this.getFolderAbsURL() + '/search';
    }
    public static getMediaPlayerAbsUrl(): string {
        return this.getRootURL() + '/media-player'
    }
    public static getMediaPlayerPlaylistAbsUrl(id: string): string {
        return this.getRootURL() + '/media-player/playlists/'+id.toString();
    }
    public static getSettingsAbsUrl(): string {
        return this.getRootURL() + '/settings'
    }
    public static getUserSettingsRelUrl(): string {
        return 'user'
    }
    public static getNetworkSettingsRelUrl(): string {
        return 'network'
    }
    public static getSystemSettingsRelUrl(): string {
        return 'system'
    }
}
