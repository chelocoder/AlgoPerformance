param([switch]$Test)
$ErrorActionPreference='Stop'
if (!$env:ALGOPERFORMANCE_JDK_HOME) { throw 'Defina ALGOPERFORMANCE_JDK_HOME para el proceso.' }
$jdk=(Resolve-Path -LiteralPath $env:ALGOPERFORMANCE_JDK_HOME).Path
$root=Split-Path -Parent $PSScriptRoot
$out=Join-Path $root '.local/phase08r'
$classes=Join-Path $out ('classes-' + [Guid]::NewGuid().ToString('N'))
$null=New-Item -ItemType Directory -Path $classes -Force
$shared=Join-Path $root 'instrument/src/main/java/pe/algoperformance/instrument'
$sources=foreach ($component in 'algorithms','inputs','catalog') {
    Get-ChildItem -LiteralPath (Join-Path $shared $component) -Filter '*.java' | ForEach-Object FullName
}
$sources += Join-Path $shared 'runner/WindowsAffinity.java'
$sources += Get-ChildItem -LiteralPath (Join-Path $root 'direct/src') -Filter '*.java' | ForEach-Object FullName
$sources += Join-Path $PSScriptRoot 'src/Candidate.java'
& "$jdk/bin/javac.exe" --release 25 -encoding UTF-8 -d $classes @sources
if ($LASTEXITCODE) { throw 'Falló javac.' }
$jar=Join-Path $out 'AlgoPerformance-v1.0.0-rc.2.jar'
& "$jdk/bin/jar.exe" --create --file $jar --main-class pe.algoperformance.direct.Candidate -C $classes .
if ($LASTEXITCODE) { throw 'Falló jar.' }
if ($Test) {
    & "$jdk/bin/javac.exe" --release 25 -encoding UTF-8 -cp $classes -d $classes (Join-Path $root 'direct/test/FunctionalTest.java')
    if ($LASTEXITCODE) { throw 'Falló compilación de pruebas.' }
    & "$jdk/bin/java.exe" -Xint -ea -cp $classes pe.algoperformance.direct.FunctionalTest
    if ($LASTEXITCODE) { throw 'Fallaron las comprobaciones funcionales.' }
}
Get-FileHash -LiteralPath $jar

