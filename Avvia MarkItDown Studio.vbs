Option Explicit
Dim shell, files, pythonw, studio, quote, errorMessage
Set shell = CreateObject("WScript.Shell")
Set files = CreateObject("Scripting.FileSystemObject")
pythonw = shell.ExpandEnvironmentStrings("%USERPROFILE%\markitdown-env\Scripts\pythonw.exe")
studio = files.BuildPath(files.GetParentFolderName(WScript.ScriptFullName), "studio.py")
quote = Chr(34)

If Not files.FileExists(pythonw) Or Not files.FileExists(studio) Then
    MsgBox "Ambiente Python o sorgente mancante. Consulta README.md.", 48, "MarkItDown Studio"
    WScript.Quit 1
End If

On Error Resume Next
shell.Run quote & pythonw & quote & " " & quote & studio & quote, 1, False
errorMessage = Err.Description
On Error GoTo 0
If Len(errorMessage) > 0 Then
    MsgBox errorMessage, 48, "MarkItDown Studio"
    WScript.Quit 1
End If
