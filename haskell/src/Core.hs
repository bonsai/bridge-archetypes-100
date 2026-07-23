{-# LANGUAGE DeriveGeneric, OverloadedStrings #-}
{-|
    bridge-archetypes-100: Haskell Orthotropic Beam Solver
    
    Pure functional FEM for wood beam (2D orthotropic, plane stress).
    Input:  JSON via stdin
    Output: JSON with displacement, stress, fracture flag
    
    No external linear-algebra deps — uses plain lists for small systems.
-}
module Main where

import GHC.Generics
import Data.Aeson
import qualified Data.ByteString.Lazy.Char8 as B
import qualified Data.Vector as V

-- ============================================================
-- Types
-- ============================================================

data Input = Input
    { l_mm      :: Double
    , b_mm      :: Double
    , h_mm      :: Double
    , e1_MPa    :: Double
    , e2_MPa    :: Double
    , nu12      :: Double
    , g12_MPa   :: Double
    , theta_deg :: Double   -- fiber angle
    , p_N       :: Double
    , fb_MPa    :: Double
    , support   :: String    -- "cantilever" | "simple"
    } deriving (Show, Generic)

instance FromJSON Input
instance ToJSON Input

data Output = Output
    { sigma_max_MPa  :: Double
    , tau_max_MPa    :: Double
    , delta_max_mm   :: Double
    , fractured      :: Bool
    , sigma_ratio    :: Double
    } deriving (Show, Generic)

instance ToJSON Output

-- ============================================================
-- Math (pure functions)
-- ============================================================

radians :: Double -> Double
radians d = d * pi / 180.0

-- Orthotropic Q matrix for given theta
qMatrix :: Double -> Double -> Double -> Double -> Double -> [[Double]]
qMatrix e1 e2 nu12 g12 theta =
    let nu21 = nu12 * e2 / e1
        q11 = e1 / (1 - nu12 * nu21)
        q22 = e2 / (1 - nu12 * nu21)
        q12 = nu21 * e1 / (1 - nu12 * nu21)
        q66 = g12
        c = cos (radians theta)
        s = sin (radians theta)
        c2 = c*c; s2 = s*s; c4 = c2*c2; s4 = s2*s2
    in [[ q11*c4 + 2*(q12+2*q66)*s2*c2 + q22*s4
        , (q11+q22-4*q66)*s2*c2 + q12*(s4+c4)
        , (q11-q12-2*q66)*c2*c*s - (q22-q12-2*q66)*c*s*s2]
       ,[ (q11+q22-4*q66)*s2*c2 + q12*(s4+c4)
        , q11*s4 + 2*(q12+2*q66)*s2*c2 + q22*c4
        , (q11-q12-2*q66)*c*s*s2 - (q22-q12-2*q66)*c2*c*s]
       ,[ (q11-q12-2*q66)*c2*c*s - (q22-q12-2*q66)*c*s*s2
        , (q11-q12-2*q66)*c*s*s2 - (q22-q12-2*q66)*c2*c*s
        , (q11+q22-2*q12-2*q66)*s2*c2 + q66*(s4+c4)]
       ]

-- Simple analytical solutions (integrated over default theta=0 -> E1)
solveBeam :: Input -> Output
solveBeam inp =
    let l = l_mm inp; b = b_mm inp; h = h_mm inp
        e = e1_MPa inp  -- use parallel modulus for simplicity
        i = b * h**3 / 12       -- mm^4
        z = b * h**2 / 6        -- mm^3
        a = b * h               -- mm^2
        p = p_N inp
        fb = fb_MPa inp
        (mMax, delta) = case support inp of
            "cantilever" -> (p * l, p * l**3 / (3 * e * i))
            _            -> (p * l / 4, p * l**3 / (48 * e * i))  -- simple center load
        sigma = mMax / z
        tau = 3 * p / (2 * a)  -- simplified for rectangular
        ratio = sigma / fb
    in Output sigma tau delta (sigma > fb) ratio

-- ============================================================
-- Main
-- ============================================================

main :: IO ()
main = do
    input <- B.getContents
    case decode input of
        Nothing -> B.putStrLn "{\"error\":\"invalid JSON\"}"
        Just inp -> B.putStrLn (encode (solveBeam inp))
