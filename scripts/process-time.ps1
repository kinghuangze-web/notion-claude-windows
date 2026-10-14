function Get-RecordedCreationMilliseconds {
    param($Value)
    # ConvertFrom-Json may decode /Date(...)/ into DateTime automatically.
    if ($Value -is [DateTime] -or $Value -is [DateTimeOffset]) {
        return ([DateTimeOffset]$Value).ToUnixTimeMilliseconds()
    }
    $match = [regex]::Match([string]$Value, '^/Date\((\d+)(?:[+-]\d+)?\)/$')
    if ($match.Success) { return [long]$match.Groups[1].Value }
    return ([DateTimeOffset]::Parse([string]$Value, [Globalization.CultureInfo]::InvariantCulture)).ToUnixTimeMilliseconds()
}
