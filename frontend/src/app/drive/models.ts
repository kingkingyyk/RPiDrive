import { Subscription } from 'rxjs';

export interface GetStorageProviderTypesResponse {
    values: StorageProviderType []
}

export interface StorageProviderType {
    name: string;
    value: string;
}

export class StorageProvider {
    id: number;
    name: string;
    type: string;
    path: string;
    usedSpace: number;
    totalSpace: number;
    rootFolder: string;
    indexing: boolean;

    construct(data: any) {
        this.id = data['id'];
        this.name = data['name'];
        this.type = data['type'];
        this.path = data['path'];
    }
}

export class InitializeSystem {
    user: User;
    storage: StorageProvider;
    initKey: string;
}

export class User {
    id: number;
    username: string;
    password: string;
    firstName: string;
    lastName: string;
    email: string;
    isActive: boolean;
    isSuperuser: boolean;
    lastLogin: string;
}

export interface IsLoggedInResponse {
    result: boolean;
}

export class Login {
    username: string;
    password: string;
}

export interface GetStorageProvidersResponse {
    values: StorageProvider[];
}

export abstract class FileObjectType {
    static readonly FOLDER = 'FOLDER';
    static readonly FILE = 'FILE';
}

export abstract class FileExt {
    static readonly TYPE_MOVIE = 'movie';
    static readonly TYPE_MUSIC = 'music';
    static readonly TYPE_PICTURE = 'picture';
    static readonly TYPE_CODE = 'code';
    static readonly TYPE_COMPRESSED = 'compressed';
    static readonly TYPE_EXECUTABLE = 'executable';
    static readonly TYPE_LIBRARY = 'library';
    static readonly TYPE_BOOK = 'book';
}

export class FileObject {
    selected: boolean = false;
    position: number;
    id: string;
    name: string;
    objType: string;
    relPath: string;
    extension: string;
    type: string;
    lastModified: string;
    size: number;
    parent: FileObject;
    trace: FileObject[];
    storageProvider: StorageProvider;
    children: FileObject[];
    metadata: Metadata;
    fullPath: string;
}

export class FileUploadModel {
    data: File;
    state: string;
    inProgress: boolean;
    progress: number;
    canRetry: boolean;
    canCancel: boolean;
    sub?: Subscription;
}

export abstract class FilePreviewType {
    private static readonly EXT_MOVIE: string[] = ['mp4', 'webm'];
    private static readonly EXT_MUSIC: string[] = ['mp3', 'm4a', 'ogg', 'flac'];
    private static readonly EXT_PICTURE: string[] = ['jpg', 'bmp', 'gif', 'png'];
    private static readonly EXT_CODE: string[] = ['cpp', 'java', 'py', 'php', 'cs', 'txt'];
    
    public static readonly MOVIE: string = 'movie';
    public static readonly MUSIC: string = 'music';
    public static readonly PICTURE: string = 'picture';
    public static readonly CODE: string = 'code';

    private static EXT_DICT: {[key: string]: string} = null;

    public static getFilePreviewType(file_ext: string) {
        if (!FilePreviewType.EXT_DICT) {
            FilePreviewType.EXT_DICT = {};
            for (let ext of FilePreviewType.EXT_MOVIE) FilePreviewType.EXT_DICT[ext] = FilePreviewType.MOVIE;
            for (let ext of FilePreviewType.EXT_MUSIC) FilePreviewType.EXT_DICT[ext] = FilePreviewType.MUSIC;
            for (let ext of FilePreviewType.EXT_PICTURE) FilePreviewType.EXT_DICT[ext] = FilePreviewType.PICTURE;
            for (let ext of FilePreviewType.EXT_CODE) FilePreviewType.EXT_DICT[ext] = FilePreviewType.CODE;
        }
        return FilePreviewType.EXT_DICT[file_ext];
    }
}

export abstract class Metadata {
    title: string;
    artist: string;
    album: string;
}

export interface SearchResultResponse {
    values: FileObject[],
    totalPages: number
}

export class Playlist {
    id: string;
    name: string;
    files: FileObject[];
}

export class GetPlaylistsResponse {
    values: Playlist[];
}

export interface NetworkUsage {
    downloadSpeed: number;
    downloadTotal: number;
    uploadSpeed: number;
    uploadTotal: number;
}

export interface SystemInfo {
    cpuCount: number;
    cpuFrequency: number[];
    cpuUsage: number;
    memTotal: number;
    memUsed: number;
    memUsage: number;
    disks: SystemInfoDisk[];
    osName: string;
    osArch: string;
    pythonVersion: string;
}

export interface SystemInfoDisk {
    path: string;
    total: number;
    used: number;
    free: number;
    percent: number;
}

export interface GetUsersResponse {
    values: User[];
}
