```text
VariableName                     Description (EN)                                                     Description (FR)
----------------------------------------------------------------------------------------------------------------------
AirDensity                       Density of air at start/finish line, kg/m^3                          Densité de l’air à la ligne de départ/arrivée, kg/m³
AirPressure                      Pressure of air at start/finish line, Pa                             Pression de l’air à la ligne de départ/arrivée, Pa
AirTemp                          Temperature of air at start/finish line, C                           Température de l’air à la ligne de départ/arrivée, °C
Brake                            0=brake released to 1=max pedal force, %                             0=frein relâché à 1=force de pédale maximale, %
BrakeABSactive                   true if abs is currently reducing brake force pressure,              Vrai si l’ABS réduit actuellement la pression de freinage
BrakeRaw                         Raw brake input 0=brake released to 1=max pedal force, %             Entrée de frein brute 0=frein relâché à 1=force de pédale maximale, %
CamCameraNumber                  Active camera number,                                                Numéro de la caméra active
CamCameraState                   State of camera system, irsdk_CameraState                            État du système de caméras, irsdk_°CameraState
CamCarIdx                        Active camera's focus car index,                                     Index de la voiture ciblée par la caméra active
CamGroupNumber                   Active camera group number,                                          Numéro du groupe de caméras actif
CarDistAhead                     Distance to first car in front of player in meters, m                Distance à la première voiture devant le pilote (en mètres), m
CarDistBehind                    Distance to first car behind player in meters, m                     Distance à la première voiture derrière le pilote (en mètres), m
CarIdxBestLapNum                 Cars best lap number,                                                Numéro du meilleur tour par voiture
CarIdxBestLapTime                Cars best lap time, s                                                Meilleur temps au tour par voiture, s
CarIdxClass                      Cars class id by car index,                                          Identifiant de classe par index de voiture
CarIdxClassPosition              Cars class position in race by car index,                            Position de classe en course (par index de voiture)
CarIdxEstTime                    Estimated time to reach current location on track, s                 Estimated temps to reach courant location sur piste, s
CarIdxF2Time                     Race time behind leader or fastest lap time otherwise, s             Course temps behind leader or fastest tour temps otherwise, s
CarIdxFastRepairsUsed            How many fast repairs each car has used,                             Combien de fast repairs each voiture has utilisés
CarIdxGear                       -1=reverse  0=neutral  1..n=current gear by car index,               -1=reverse 0=neutral 1..n=courant rapport by voiture index
CarIdxLap                        Laps started by car index,                                           Tours started by voiture index
CarIdxLapCompleted               Laps completed by car index,                                         Tours completed by voiture index
CarIdxLapDistPct                 Percentage distance around lap by car index, %                       Pourcentage de distance parcourue dans le tour by voiture index, %
CarIdxLastLapTime                Cars last lap time, s                                                Voitures last tour temps, s
CarIdxOnPitRoad                  On pit road between the cones by car index,                          Sur stand road between the cones by voiture index
CarIdxP2P_Count                  Push2Pass count of usage (or remaining in Race),                     Push2Pass count of usage (or restant in Course)
CarIdxP2P_Status                 Push2Pass active or not,                                             Push2Pass active or not
CarIdxPaceFlags                  Pacing status flags for each car, irsdk_PaceFlags                    Pacing status flags for each voiture, irsdk_Pace°Flags
CarIdxPaceLine                   What line cars are pacing in  or -1 if not pacing,                   What conduite voitures sont pacing in or -1 if not pacing
CarIdxPaceRow                    What row cars are pacing in  or -1 if not pacing,                    What row voitures sont pacing in or -1 if not pacing
CarIdxPosition                   Cars position in race by car index,                                  Voitures position in course by voiture index
CarIdxQualTireCompound           Cars Qual tire compound,                                             Voitures Qual pneu compound
CarIdxQualTireCompoundLocked     Cars Qual tire compound is locked-in,                                Voitures Qual pneu compound is locked-in
CarIdxRPM                        Engine rpm by car index, revs/min                                    Régime moteur by voiture index, tr/min
CarIdxSessionFlags               Session flags for each player, irsdk_Flags                           Session flags for each pilote, irsdk_°Flags
CarIdxSteer                      Steering wheel angle by car index, rad                               Steering wheel angle by voiture index, rad
CarIdxTireCompound               Cars current tire compound,                                          Voitures courant pneu compound
CarIdxTrackSurface               Track surface type by car index, irsdk_TrkLoc                        Piste surface type by voiture index, irsdk_TrkLoc
CarIdxTrackSurfaceMaterial       Track surface material type by car index, irsdk_TrkSurf              Piste surface material type by voiture index, irsdk_TrkSurf
CarLeftRight                     Notify if car is to the left or right of driver, irsdk_CarLeftRight  Notify if voiture is to the gauche or droite of pilote, irsdk_°CarLeftRight
ChanAvgLatency                   Communications average latency, s                                    Communications average latency, s
ChanClockSkew                    Communications server clock skew, s                                  Communications server clock skew, s
ChanLatency                      Communications latency, s                                            Communications latency, s
ChanPartnerQuality               Partner communications quality, %                                    Partner communications quality, %
ChanQuality                      Communications quality, %                                            Communications quality, %
Clutch                           0=disengaged to 1=fully engaged, %                                   0=disengaged to 1=fully engaged, %
ClutchRaw                        Raw clutch input 0=disengaged to 1=fully engaged, %                  Raw embrayage input 0=disengaged to 1=fully engaged, %
CpuUsageBG                       Percent of available tim bg thread took with a 1 sec avg, %          Pourcentage of disponibles tim bg thread took with a 1 sec avg, %
CpuUsageFG                       Percent of available tim fg thread took with a 1 sec avg, %          Pourcentage of disponibles tim fg thread took with a 1 sec avg, %
DCDriversSoFar                   Number of team drivers who have run a stint,                         Numéro of team drivers who have run a stint
DCLapStatus                      Status of driver change lap requirements,                            Status of pilote change tour requirements
dcPitSpeedLimiterToggle          Track if pit speed limiter system is enabled,                        Piste if stand speed limiter system is enabled
dcStarter                        In car trigger car starter,                                          In voiture trigger voiture starter
dcToggleWindshieldWipers         In car turn wipers on or off,                                        In voiture turn wipers sur or off
dcTriggerWindshieldWipers        In car momentarily turn on wipers,                                   In voiture momentarily turn sur wipers
DisplayUnits                     Default units for the user interface 0 = english 1 = metric,         Default unités for the user interface 0 = english 1 = metric
dpFastRepair                     Pitstop fast repair set,                                             Pitstop fast repair réglés
dpFuelAddKg                      Pitstop fuel add amount, kg                                          Pitstop fuel add amount, kg
dpFuelAutoFillActive             Pitstop auto fill fuel next stop flag,                               Pitstop auto fill fuel next stop flag
dpFuelAutoFillEnabled            Pitstop auto fill fuel system enabled,                               Pitstop auto fill fuel system enabled
dpFuelFill                       Pitstop fuel fill flag,                                              Pitstop fuel fill flag
dpLFTireChange                   Pitstop lf tire change request,                                      Pitstop lf pneu change request
dpLFTireColdPress                Pitstop lf tire cold pressure adjustment, Pa                         Pitstop lf pneu cold pression adjustment, Pa
dpLRTireChange                   Pitstop lr tire change request,                                      Pitstop lr pneu change request
dpLRTireColdPress                Pitstop lr tire cold pressure adjustment, Pa                         Pitstop lr pneu cold pression adjustment, Pa
dpRFTireChange                   Pitstop rf tire change request,                                      Pitstop rf pneu change request
dpRFTireColdPress                Pitstop rf cold tire pressure adjustment, Pa                         Pitstop rf cold pneu pression adjustment, Pa
dpRRTireChange                   Pitstop rr tire change request,                                      Pitstop rr pneu change request
dpRRTireColdPress                Pitstop rr cold tire pressure adjustment, Pa                         Pitstop rr cold pneu pression adjustment, Pa
dpWindshieldTearoff              Pitstop windshield tearoff,                                          Pitstop windshield tearoff
DriverMarker                     Driver activated flag,                                               Pilote activated flag
Engine0_RPM                      Engine0Engine rpm, revs/min                                          Moteur0Moteur tr/min, tr/min
EngineWarnings                   Bitfield for warning lights, irsdk_EngineWarnings                    Bitfield for avertissement lights, irsdk_EngineWarnings
EnterExitReset                   Indicate action the reset key will take 0 enter 1 exit 2 reset,      Indicate action the reset key will take 0 enter 1 exit 2 reset
FastRepairAvailable              How many fast repairs left  255 is unlimited,                        Combien de fast repairs gauche 255 is illimité
FastRepairUsed                   How many fast repairs used so far,                                   Nombre de fast repairs utilisés jusqu’à présent
FogLevel                         Fog level at start/finish line, %                                    Brouillard level at départ/arrivée conduite, %
FrameRate                        Average frames per second, fps                                       Average frames par second, fps
FrontTireSetsAvailable           How many front tire sets are remaining  255 is unlimited,            Nombre de avant pneu sets restants ; 255 = illimité
FrontTireSetsUsed                How many front tire sets used so far,                                Nombre de avant pneu sets utilisés jusqu’à présent
FuelLevel                        Liters of fuel remaining, l                                          Liters of fuel restant, l
FuelLevelPct                     Percent fuel remaining, %                                            Pourcentage fuel restant, %
FuelPress                        Engine fuel pressure, bar                                            Moteur fuel pression, bar
FuelUsePerHour                   Engine fuel used instantaneous, kg/h                                 Moteur fuel utilisés instantaneous, kg/h
Gear                             -1=reverse  0=neutral  1..n=current gear,                            -1=reverse 0=neutral 1..n=courant rapport
GpuUsage                         Percent of available tim gpu took with a 1 sec avg, %                Pourcentage of disponibles tim gpu took with a 1 sec avg, %
HandbrakeRaw                     Raw handbrake input 0=handbrake released to 1=max force, %           Raw handbrake input 0=handbrake relâché to 1=max force, %
IsDiskLoggingActive              0=disk based telemetry file not being written  1=being written,      0=disk based telemetry file not son written 1=son written
IsDiskLoggingEnabled             0=disk based telemetry turned off  1=turned on,                      0=disk based telemetry turned off 1=turned sur
IsGarageVisible                  1=Garage screen is visible,                                          1=Garage screen is visible
IsInGarage                       1=Car in garage physics running,                                     1=Voiture in garage physics running
IsOnTrack                        1=Car on track physics running with player in car,                   1=Voiture sur piste physics running with pilote in voiture
IsOnTrackCar                     1=Car on track physics running,                                      1=Voiture sur piste physics running
IsReplayPlaying                  0=replay not playing  1=replay playing,                              0=replay not playing 1=replay playing
Lap                              Laps started count,                                                  Tours started count
LapBestLap                       Players best lap number,                                             Players best tour numéro
LapBestLapTime                   Players best lap time, s                                             Players best tour temps, s
LapBestNLapLap                   Player last lap in best N average lap time,                          Pilote last tour in best N average tour temps
LapBestNLapTime                  Player best N average lap time, s                                    Pilote best N average tour temps, s
LapCompleted                     Laps completed count,                                                Tours completed count
LapCurrentLapTime                Estimate of players current lap time as shown in F3 box, s           Estimate of players courant tour temps tels shown in F3 box, s
LapDeltaToBestLap                Delta time for best lap, s                                           Delta temps for best tour, s
LapDeltaToBestLap_DD             Rate of change of delta time for best lap, s/s                       Taux de variation de delta temps for best tour, s/s
LapDeltaToBestLap_OK             Delta time for best lap is valid,                                    Delta temps for best tour is valide
LapDeltaToOptimalLap             Delta time for optimal lap, s                                        Delta pour le tour optimal, s
LapDeltaToOptimalLap_DD          Rate of change of delta time for optimal lap, s/s                    Taux de variation de Delta pour le tour optimal, s/s
LapDeltaToOptimalLap_OK          Delta time for optimal lap is valid,                                 Le delta du tour optimal est valide
LapDeltaToSessionBestLap         Delta time for session best lap, s                                   Delta par rapport au meilleur tour de la session, s
LapDeltaToSessionBestLap_DD      Rate of change of delta time for session best lap, s/s               Taux de variation de Delta par rapport au meilleur tour de la session, s/s
LapDeltaToSessionBestLap_OK      Delta time for session best lap is valid,                            Le delta par rapport au meilleur tour de la session est valide
LapDeltaToSessionLastlLap        Delta time for session last lap, s                                   Delta par rapport au dernier tour de la session, s
LapDeltaToSessionLastlLap_DD     Rate of change of delta time for session last lap, s/s               Taux de variation de Delta par rapport au dernier tour de la session, s/s
LapDeltaToSessionLastlLap_OK     Delta time for session last lap is valid,                            Le delta par rapport au dernier tour de la session est valide
LapDeltaToSessionOptimalLap      Delta time for session optimal lap, s                                Delta par rapport au tour optimal de la session, s
LapDeltaToSessionOptimalLap_DD   Rate of change of delta time for session optimal lap, s/s            Taux de variation de Delta par rapport au tour optimal de la session, s/s
LapDeltaToSessionOptimalLap_OK   Delta time for session optimal lap is valid,                         Le delta par rapport au tour optimal de la session est valide
LapDist                          Meters traveled from S/F this lap, m                                 Mètres parcourus depuis la ligne S/F dans ce tour, m
LapDistPct                       Percentage distance around lap, %                                    Pourcentage de distance parcourue dans le tour, %
LapLasNLapSeq                    Player num consecutive clean laps completed for N average,           Pilote num consecutive clean tours completed for N average
LapLastLapTime                   Players last lap time, s                                             Temps du dernier tour du pilote, s
LapLastNLapTime                  Player last N average lap time, s                                    Pilote last N average tour temps, s
LatAccel                         Lateral acceleration (including gravity), m/s^2                      Lateral accélération (including gravity), m/s^2
LatAccel_ST                      Lateral acceleration (including gravity) at 360 Hz, m/s^2            Lateral accélération (including gravity) à 360 Hz, m/s^2
LeftTireSetsAvailable            How many left tire sets are remaining  255 is unlimited,             Nombre de gauche pneu sets restants ; 255 = illimité
LeftTireSetsUsed                 How many left tire sets used so far,                                 Nombre de gauche pneu sets utilisés jusqu’à présent
LFbrakeLinePress                 LF brake line pressure, bar                                          LF pression de la conduite de frein, bar
LFcoldPressure                   LF tire cold pressure  as set in the garage, kPa                     LF pneu cold pression tels que réglés dans le garage, kPa
LFodometer                       LF distance tire traveled since being placed on car, m               LF distance parcourue par le pneu depuis son montage sur la voiture, m
LFshockDefl                      LF shock deflection, m                                               LF déflexion d’amortisseur, m
LFshockDefl_ST                   LF shock deflection at 360 Hz, m                                     LF déflexion d’amortisseur à 360 Hz, m
LFshockVel                       LF shock velocity, m/s                                               LF vitesse d’amortisseur, m/s
LFshockVel_ST                    LF shock velocity at 360 Hz, m/s                                     LF vitesse d’amortisseur à 360 Hz, m/s
LFtempCL                         LF tire left carcass temperature, C                                  LF température de la carcasse du pneu (zone gauche), °C
LFtempCM                         LF tire middle carcass temperature, C                                LF température de la carcasse du pneu (zone middle), °C
LFtempCR                         LF tire right carcass temperature, C                                 LF température de la carcasse du pneu (zone droite), °C
LFTiresAvailable                 How many left front tires are remaining  255 is unlimited,           Nombre de gauche avant pneus restants ; 255 = illimité
LFTiresUsed                      How many left front tires used so far,                               Nombre de gauche avant pneus utilisés jusqu’à présent
LFwearL                          LF tire left percent tread remaining, %                              LF pneu gauche pourcentage de bande de roulement restante, %
LFwearM                          LF tire middle percent tread remaining, %                            LF pneu middle pourcentage de bande de roulement restante, %
LFwearR                          LF tire right percent tread remaining, %                             LF pneu droite pourcentage de bande de roulement restante, %
LoadNumTextures                  True if the car_num texture will be loaded,                          Vrai if the voiture_num texture will be loaded
LongAccel                        Longitudinal acceleration (including gravity), m/s^2                 Longitudinal accélération (including gravity), m/s^2
LongAccel_ST                     Longitudinal acceleration (including gravity) at 360 Hz, m/s^2       Longitudinal accélération (including gravity) à 360 Hz, m/s^2
LRbrakeLinePress                 LR brake line pressure, bar                                          LR pression de la conduite de frein, bar
LRcoldPressure                   LR tire cold pressure  as set in the garage, kPa                     LR pneu cold pression tels que réglés dans le garage, kPa
LRodometer                       LR distance tire traveled since being placed on car, m               LR distance parcourue par le pneu depuis son montage sur la voiture, m
LRshockDefl                      LR shock deflection, m                                               LR déflexion d’amortisseur, m
LRshockDefl_ST                   LR shock deflection at 360 Hz, m                                     LR déflexion d’amortisseur à 360 Hz, m
LRshockVel                       LR shock velocity, m/s                                               LR vitesse d’amortisseur, m/s
LRshockVel_ST                    LR shock velocity at 360 Hz, m/s                                     LR vitesse d’amortisseur à 360 Hz, m/s
LRtempCL                         LR tire left carcass temperature, C                                  LR température de la carcasse du pneu (zone gauche), °C
LRtempCM                         LR tire middle carcass temperature, C                                LR température de la carcasse du pneu (zone middle), °C
LRtempCR                         LR tire right carcass temperature, C                                 LR température de la carcasse du pneu (zone droite), °C
LRTiresAvailable                 How many left rear tires are remaining  255 is unlimited,            Nombre de gauche arrière pneus restants ; 255 = illimité
LRTiresUsed                      How many left rear tires used so far,                                Nombre de gauche arrière pneus utilisés jusqu’à présent
LRwearL                          LR tire left percent tread remaining, %                              LR pneu gauche pourcentage de bande de roulement restante, %
LRwearM                          LR tire middle percent tread remaining, %                            LR pneu middle pourcentage de bande de roulement restante, %
LRwearR                          LR tire right percent tread remaining, %                             LR pneu droite pourcentage de bande de roulement restante, %
ManifoldPress                    Engine manifold pressure, bar                                        Moteur manifold pression, bar
ManualBoost                      Hybrid manual boost state,                                           Hybrid manual boost state
ManualNoBoost                    Hybrid manual no boost state,                                        Hybrid manual no boost state
MemPageFaultSec                  Memory page faults per second,                                       Memory page faults par second
MemSoftPageFaultSec              Memory soft page faults per second,                                  Memory soft page faults par second
OilLevel                         Engine oil level, l                                                  Moteur oil level, l
OilPress                         Engine oil pressure, bar                                             Moteur oil pression, bar
OilTemp                          Engine oil temperature, C                                            Moteur oil température, °C
OkToReloadTextures               True if it is ok to reload car textures at this time,                Vrai if it is ok to reload voiture textures at this temps
OnPitRoad                        Is the player car on pit road between the cones,                     Is the pilote voiture sur stand road between the cones
P2P_Count                        Push2Pass count of usage (or remaining in Race) on your car,         Push2Pass count of usage (or restant in Course) sur your voiture
P2P_Status                       Push2Pass active or not on your car,                                 Push2Pass active or not sur your voiture
PaceMode                         Are we pacing or not, irsdk_PaceMode                                 Sont we pacing or not, irsdk_PaceMode
Pitch                            Pitch orientation, rad                                               Orientation de tangage, rad
PitchRate                        Pitch rate, rad/s                                                    Vitesse de tangage, rad/s
PitchRate_ST                     Pitch rate at 360 Hz, rad/s                                          Vitesse de tangage à 360 Hz, rad/s
PitOptRepairLeft                 Time left for optional repairs if repairs are active, s              Temps gauche for optional repairs if repairs sont active, s
PitRepairLeft                    Time left for mandatory pit repairs if repairs are active, s         Temps gauche for mandatory stand repairs if repairs sont active, s
PitsOpen                         True if pit stop is allowed for the current player,                  Vrai if stand stop is allowed for the courant pilote
PitstopActive                    Is the player getting pit stop service,                              Is the pilote getting stand stop service
PitSvFlags                       Bitfield of pit service checkboxes, irsdk_PitSvFlags                 Bitfield of stand service checkboxes, irsdk_PitSv°Flags
PitSvFuel                        Pit service fuel add amount, l or kWh                                Stand service fuel add amount, l or kWh
PitSvLFP                         Pit service left front tire pressure, kPa                            Stand service gauche avant pneu pression, kPa
PitSvLRP                         Pit service left rear tire pressure, kPa                             Stand service gauche arrière pneu pression, kPa
PitSvRFP                         Pit service right front tire pressure, kPa                           Stand service droite avant pneu pression, kPa
PitSvRRP                         Pit service right rear tire pressure, kPa                            Stand service droite arrière pneu pression, kPa
PitSvTireCompound                Pit service pending tire compound,                                   Stand service pending pneu compound
PlayerCarClass                   Player car class id,                                                 Pilote voiture classe identifiant
PlayerCarClassPosition           Players class position in race,                                      Players classe position in course
PlayerCarDriverIncidentCount     Teams current drivers incident count for this session,               Teams courant drivers incident count for this session
PlayerCarDryTireSetLimit         Players dry tire set limit,                                          Players dry pneu réglés limite
PlayerCarIdx                     Players carIdx,                                                      Players carIdx
PlayerCarInPitStall              Players car is properly in their pitstall,                           Players voiture is properly in their pitstall
PlayerCarMyIncidentCount         Players own incident count for this session,                         Players own incident count for this session
PlayerCarPitSvStatus             Players car pit service status bits, irsdk_PitSvStatus               Players voiture stand service status bits, irsdk_PitSvStatus
PlayerCarPosition                Players position in race,                                            Players position in course
PlayerCarPowerAdjust             Players power adjust, %                                              Players puissance adjust, %
PlayerCarSLBlinkRPM              Shift light blink rpm, revs/min                                      Shift light blink tr/min, tr/min
PlayerCarSLFirstRPM              Shift light first light rpm, revs/min                                Shift light first light tr/min, tr/min
PlayerCarSLLastRPM               Shift light last light rpm, revs/min                                 Shift light last light tr/min, tr/min
PlayerCarSLShiftRPM              Shift light shift rpm, revs/min                                      Shift light shift tr/min, tr/min
PlayerCarTeamIncidentCount       Players team incident count for this session,                        Players team incident count for this session
PlayerCarTowTime                 Players car is being towed if time is greater than zero, s           Players voiture is son towed if temps is greater than zero, s
PlayerCarWeightPenalty           Players weight penalty, kg                                           Players weight penalty, kg
PlayerFastRepairsUsed            Players car number of fast repairs used,                             Players voiture numéro of fast repairs utilisés
PlayerIncidents                  Log incidents that the player recieved, irsdk_IncidentFlags          Log incidents that the pilote recieved, irsdk_Incident°Flags
PlayerTireCompound               Players car current tire compound,                                   Players voiture courant pneu compound
PlayerTrackSurface               Players car track surface type, irsdk_TrkLoc                         Players voiture piste surface type, irsdk_TrkLoc
PlayerTrackSurfaceMaterial       Players car track surface material type, irsdk_TrkSurf               Players voiture piste surface material type, irsdk_TrkSurf
Precipitation                    Precipitation at start/finish line, %                                Precipitation at départ/arrivée conduite, %
PushToPass                       Push to pass button state,                                           Push to pass button state
PushToTalk                       Push to talk button state,                                           Push to talk button state
RaceLaps                         Laps completed in race,                                              Tours completed in course
RadioTransmitCarIdx              The car index of the current person speaking on the radio,           The voiture index of the courant person speaking sur the radio
RadioTransmitFrequencyIdx        The frequency index of the current person speaking on the radio,     The frequency index of the courant person speaking sur the radio
RadioTransmitRadioIdx            The radio index of the current person speaking on the radio,         The radio index of the courant person speaking sur the radio
RearTireSetsAvailable            How many rear tire sets are remaining  255 is unlimited,             Nombre de arrière pneu sets restants ; 255 = illimité
RearTireSetsUsed                 How many rear tire sets used so far,                                 Nombre de arrière pneu sets utilisés jusqu’à présent
RelativeHumidity                 Relative Humidity at start/finish line, %                            Relative Humidité at départ/arrivée conduite, %
ReplayFrameNum                   Integer replay frame number (60 per second),                         Integer replay frame numéro (60 par second)
ReplayFrameNumEnd                Integer replay frame number from end of tape,                        Integer replay frame numéro from end of tape
ReplayPlaySlowMotion             0=not slow motion  1=replay is in slow motion,                       0=not slow motion 1=replay is in slow motion
ReplayPlaySpeed                  Replay playback speed,                                               Replay playback speed
ReplaySessionNum                 Replay session number,                                               Replay session numéro
ReplaySessionTime                Seconds since replay session start, s                                Seconds depuis replay session start, s
RFbrakeLinePress                 RF brake line pressure, bar                                          RF pression de la conduite de frein, bar
RFcoldPressure                   RF tire cold pressure  as set in the garage, kPa                     RF pneu cold pression tels que réglés dans le garage, kPa
RFodometer                       RF distance tire traveled since being placed on car, m               RF distance parcourue par le pneu depuis son montage sur la voiture, m
RFshockDefl                      RF shock deflection, m                                               RF déflexion d’amortisseur, m
RFshockDefl_ST                   RF shock deflection at 360 Hz, m                                     RF déflexion d’amortisseur à 360 Hz, m
RFshockVel                       RF shock velocity, m/s                                               RF vitesse d’amortisseur, m/s
RFshockVel_ST                    RF shock velocity at 360 Hz, m/s                                     RF vitesse d’amortisseur à 360 Hz, m/s
RFtempCL                         RF tire left carcass temperature, C                                  RF température de la carcasse du pneu (zone gauche), °C
RFtempCM                         RF tire middle carcass temperature, C                                RF température de la carcasse du pneu (zone middle), °C
RFtempCR                         RF tire right carcass temperature, C                                 RF température de la carcasse du pneu (zone droite), °C
RFTiresAvailable                 How many right front tires are remaining  255 is unlimited,          Nombre de droite avant pneus restants ; 255 = illimité
RFTiresUsed                      How many right front tires used so far,                              Nombre de droite avant pneus utilisés jusqu’à présent
RFwearL                          RF tire left percent tread remaining, %                              RF pneu gauche pourcentage de bande de roulement restante, %
RFwearM                          RF tire middle percent tread remaining, %                            RF pneu middle pourcentage de bande de roulement restante, %
RFwearR                          RF tire right percent tread remaining, %                             RF pneu droite pourcentage de bande de roulement restante, %
RightTireSetsAvailable           How many right tire sets are remaining  255 is unlimited,            Nombre de droite pneu sets restants ; 255 = illimité
RightTireSetsUsed                How many right tire sets used so far,                                Nombre de droite pneu sets utilisés jusqu’à présent
Roll                             Roll orientation, rad                                                Orientation de roulis, rad
RollRate                         Roll rate, rad/s                                                     Vitesse de roulis, rad/s
RollRate_ST                      Roll rate at 360 Hz, rad/s                                           Vitesse de roulis à 360 Hz, rad/s
RPM                              Engine rpm, revs/min                                                 Régime moteur, tr/min
RRbrakeLinePress                 RR brake line pressure, bar                                          RR pression de la conduite de frein, bar
RRcoldPressure                   RR tire cold pressure  as set in the garage, kPa                     RR pneu cold pression tels que réglés dans le garage, kPa
RRodometer                       RR distance tire traveled since being placed on car, m               RR distance parcourue par le pneu depuis son montage sur la voiture, m
RRshockDefl                      RR shock deflection, m                                               RR déflexion d’amortisseur, m
RRshockDefl_ST                   RR shock deflection at 360 Hz, m                                     RR déflexion d’amortisseur à 360 Hz, m
RRshockVel                       RR shock velocity, m/s                                               RR vitesse d’amortisseur, m/s
RRshockVel_ST                    RR shock velocity at 360 Hz, m/s                                     RR vitesse d’amortisseur à 360 Hz, m/s
RRtempCL                         RR tire left carcass temperature, C                                  RR température de la carcasse du pneu (zone gauche), °C
RRtempCM                         RR tire middle carcass temperature, C                                RR température de la carcasse du pneu (zone middle), °C
RRtempCR                         RR tire right carcass temperature, C                                 RR température de la carcasse du pneu (zone droite), °C
RRTiresAvailable                 How many right rear tires are remaining  255 is unlimited,           Nombre de droite arrière pneus restants ; 255 = illimité
RRTiresUsed                      How many right rear tires used so far,                               Nombre de droite arrière pneus utilisés jusqu’à présent
RRwearL                          RR tire left percent tread remaining, %                              RR pneu gauche pourcentage de bande de roulement restante, %
RRwearM                          RR tire middle percent tread remaining, %                            RR pneu middle pourcentage de bande de roulement restante, %
RRwearR                          RR tire right percent tread remaining, %                             RR pneu droite pourcentage de bande de roulement restante, %
SessionFlags                     Session flags, irsdk_Flags                                           Session flags, irsdk_°Flags
SessionJokerLapsRemain           Joker laps remaining to be taken,                                    Joker tours restant to be taken
SessionLapsRemain                Old laps left till session ends use SessionLapsRemainEx,             Old tours gauche till session ends use SessionLapsRemainEx
SessionLapsRemainEx              New improved laps left till session ends,                            New improved tours gauche till session ends
SessionLapsTotal                 Total number of laps in session,                                     Total numéro of tours in session
SessionNum                       Session number,                                                      Session numéro
SessionOnJokerLap                Player is currently completing a joker lap,                          Pilote is actuellement completing a joker tour
SessionState                     Session state, irsdk_SessionState                                    Session state, irsdk_SessionState
SessionTick                      Current update number,                                               Courant update numéro
SessionTime                      Seconds since session start, s                                       Seconds depuis session start, s
SessionTimeOfDay                 Time of day in seconds, s                                            Temps of day in seconds, s
SessionTimeRemain                Seconds left till session ends, s                                    Seconds gauche till session ends, s
SessionTimeTotal                 Total number of seconds in session, s                                Total numéro of seconds in session, s
SessionUniqueID                  Session ID,                                                          Session IDENTIFIANT
Shifter                          Log inputs from the players shifter control,                         Log inputs from the players shifter control
ShiftGrindRPM                    RPM of shifter grinding noise, RPM                                   TR/MIN of shifter grinding noise, RPM
ShiftIndicatorPct                DEPRECATED use DriverCarSLBlinkRPM instead, %                        DEPRECATED use DriverCarSLBlinkRPM instead, %
ShiftPowerPct                    Friction torque applied to gears when shifting or grinding, %        Friction couple applied to gears when shifting or grinding, %
Skies                            Skies (0=clear/1=p cloudy/2=m cloudy/3=overcast),                    Ciel (0=clear/1=p cloudy/2=m cloudy/3=overcast)
SolarAltitude                    Sun angle above horizon in radians, rad                              Sun angle above horizon in radians, rad
SolarAzimuth                     Sun angle clockwise from north in radians, rad                       Sun angle clockwise from nord in radians, rad
Speed                            GPS vehicle speed, m/s                                               GPS vehicle speed, m/s
SteeringFFBEnabled               Force feedback is enabled,                                           Force feedback is enabled
SteeringWheelAngle               Steering wheel angle, rad                                            Steering wheel angle, rad
SteeringWheelAngleMax            Steering wheel max angle, rad                                        Steering wheel max angle, rad
SteeringWheelLimiter             Force feedback limiter strength limits impacts and oscillation, %    Force feedback limiter strength limits impacts and oscillation, %
SteeringWheelMaxForceNm          Value of strength or max force slider in Nm for FFB, N*m             Value of strength or max force slider in Nm for FFB, N*m
SteeringWheelPctDamper           Force feedback % max damping, %                                      Force feedback % max damping, %
SteeringWheelPctIntensity        Force feedback % max intensity, %                                    Force feedback % max intensity, %
SteeringWheelPctSmoothing        Force feedback % max smoothing, %                                    Force feedback % max smoothing, %
SteeringWheelPctTorque           Force feedback % max torque on steering shaft unsigned, %            Force feedback % max couple sur steering shaft unsigned, %
SteeringWheelPctTorqueSign       Force feedback % max torque on steering shaft signed, %              Force feedback % max couple sur steering shaft signed, %
SteeringWheelPctTorqueSignStops  Force feedback % max torque on steering shaft signed stops, %        Force feedback % max couple sur steering shaft signed stops, %
SteeringWheelPeakForceNm         Peak torque mapping to direct input units for FFB, N*m               Peak couple mapping to direct input unités for FFB, N*m
SteeringWheelTorque              Output torque on steering shaft, N*m                                 Output couple sur steering shaft, N*m
SteeringWheelTorque_ST           Output torque on steering shaft at 360 Hz, N*m                       Output couple sur steering shaft à 360 Hz, N*m
SteeringWheelUseLinear           True if steering wheel force is using linear mode,                   Vrai if steering wheel force is using linear mode
Throttle                         0=off throttle to 1=full throttle, %                                 0=off accélérateur to 1=full accélérateur, %
ThrottleRaw                      Raw throttle input 0=off throttle to 1=full throttle, %              Raw accélérateur input 0=off accélérateur to 1=full accélérateur, %
TireLF_RumblePitch               Players LF Tire Sound rumblestrip pitch, Hz                          Players LF Pneu Sound rumblestrip pitch, Hz
TireLR_RumblePitch               Players LR Tire Sound rumblestrip pitch, Hz                          Players LR Pneu Sound rumblestrip pitch, Hz
TireRF_RumblePitch               Players RF Tire Sound rumblestrip pitch, Hz                          Players RF Pneu Sound rumblestrip pitch, Hz
TireRR_RumblePitch               Players RR Tire Sound rumblestrip pitch, Hz                          Players RR Pneu Sound rumblestrip pitch, Hz
TireSetsAvailable                How many tire sets are remaining  255 is unlimited,                  Nombre de pneu sets restants ; 255 = illimité
TireSetsUsed                     How many tire sets used so far,                                      Nombre de pneu sets utilisés jusqu’à présent
TrackTemp                        Deprecated  set to TrackTempCrew, C                                  Deprecated réglés to TrackTempCrew, °C
TrackTempCrew                    Temperature of track measured by crew around track, C                Température of piste measured by crew around piste, °C
TrackWetness                     How wet is the average track surface, irsdk_TrackWetness             Combien wet is the average piste surface, irsdk_TrackWetness
VelocityX                        X velocity, m/s                                                      X vitesse, m/s
VelocityX_ST                     X velocity, m/s at 360 Hz                                            X vitesse, m/s at 360 Hz
VelocityY                        Y velocity, m/s                                                      Y vitesse, m/s
VelocityY_ST                     Y velocity, m/s at 360 Hz                                            Y vitesse, m/s at 360 Hz
VelocityZ                        Z velocity, m/s                                                      Z vitesse, m/s
VelocityZ_ST                     Z velocity, m/s at 360 Hz                                            Z vitesse, m/s at 360 Hz
VertAccel                        Vertical acceleration (including gravity), m/s^2                     Vertical accélération (including gravity), m/s^2
VertAccel_ST                     Vertical acceleration (including gravity) at 360 Hz, m/s^2           Vertical accélération (including gravity) à 360 Hz, m/s^2
VidCapActive                     True if video currently being captured,                              Vrai if video actuellement son captured
VidCapEnabled                    True if video capture system is enabled,                             Vrai if video capture system is enabled
Voltage                          Engine voltage, V                                                    Moteur tension, V
WaterLevel                       Engine coolant level, l                                              Moteur coolant level, l
WaterTemp                        Engine coolant temp, C                                               Moteur coolant temp, °C
WeatherDeclaredWet               The steward says rain tires can be used,                             The steward says rain pneus can be utilisés
WindDir                          Wind direction at start/finish line, rad                             Direction du vent à la ligne de départ/arrivée, rad
WindVel                          Wind velocity at start/finish line, m/s                              Vitesse du vent à la ligne de départ/arrivée, m/s
Yaw                              Yaw orientation, rad                                                 Orientation de lacet, rad
YawNorth                         Yaw orientation relative to north, rad                               Orientation de lacet par rapport au nord, rad
YawRate                          Yaw rate, rad/s                                                      Vitesse de lacet, rad/s
YawRate_ST                       Yaw rate at 360 Hz, rad/s                                            Vitesse de lacet à 360 Hz, rad/s
```