-- loadandrunscript startupscript()
--     -- Turn off beeper
--     beeper.enable = beeper.OFF
--     --
--     display.clear()
--     -- Restore Series 2602A defaults on ChA and ChB
--     -- Changed 9/15/16 by Jon Frost to recall setup 1 instead
--     errorqueue.clear()
--     -- Select Channel A and Channel B display formats.
--     display.screen = display.SMUA_SMUB
--     -- Display voltage measurement and sourcing for ChA and ChB.
--     smua.sense = smua.SENSE_REMOTE
--     smub.sense = smub.SENSE_REMOTE
--     --
--     display.smua.measure.func = display.MEASURE_DCVOLTS
--     display.smub.measure.func = display.MEASURE_DCVOLTS
--     smua.source.func = smua.OUTPUT_DCAMPS
--     smub.source.func = smub.OUTPUT_DCAMPS
--     -- Set the current compliance for ChA ChB
--     smua.source.limiti = 1.0
--     smub.source.limiti = 1.0
--     -- Set the voltage compliance for ChA ChB
--     smua.source.limitv = 12
--     smub.source.limitv = 12
--     -- Set measurement speed for ChA ChB
--     -- NPLC is number of power line cycles
--     -- 10 (10/60=0.16 secs) is considered high accuracy
--     smua.measure.nplc = 10
--     smub.measure.nplc = 10
--     -- Select measure V auto range.
--     smua.measure.autorangev = smua.AUTORANGE_ON
--     smub.measure.autorangev = smub.AUTORANGE_ON
--     -- open the channels
--     smua.source.output = smua.OUTPUT_HIGH_Z
--     smub.source.output = smub.OUTPUT_HIGH_Z
--     smua.source.offmode = smua.OUTPUT_HIGH_Z
--     smub.source.offmode = smub.OUTPUT_HIGH_Z
--     setup.save(1)
--     setup.poweron = 1
-- endscript

loadandrunscript startupscript()
    -- Four wire sensing ChA and ChB (4W).
    smua.sense = smua.SENSE_REMOTE
    smub.sense = smub.SENSE_REMOTE
    smua.source.output = smua.OUTPUT_HIGH_Z
    smub.source.output = smub.OUTPUT_HIGH_Z
    smua.source.offmode = smua.OUTPUT_HIGH_Z
    smub.source.offmode = smub.OUTPUT_HIGH_Z
endscript

loadscript safety()
    function safetycutoff(t)
        delay(t)
        smua.source.output = smua.OUTPUT_OFF
        smub.source.output = smub.OUTPUT_OFF
    end
endscript
display.setcursor(1,1)
display.settext("safety")
safety()